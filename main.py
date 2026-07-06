"""
Main FastAPI application
"""
import logging
import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

from config import get_config
from device_utils import detect_device, print_device_info
from rtsp_handler import RTSPStreamHandler, MockRTSPStream
from motion_detector import MotionDetector, MotionBuffer
from recording import ClipRecorder
from onedrive_manager import OneDriveManager, MockOneDrive
from notifications import FirebaseNotifications, MockFirebase

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/thinkcam.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Load config
config = get_config()
config.validate()

# Initialize FastAPI
app = FastAPI(title="ThinkCam", version="0.1.0")

# Global state
device_caps = detect_device()
stream_handler = None
motion_detector = None
motion_buffer = None
recorder = None
onedrive_manager = None
notifications = None
events_log = []

# Device info tracking
current_clip = None
last_motion_time = None


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global stream_handler, motion_detector, motion_buffer, recorder, onedrive_manager, notifications
    
    print_device_info()
    logger.info(f"🚀 Starting ThinkCam on {device_caps.device_type}")
    
    # Initialize motion detector (use device recommendations)
    detection_mode = config.detection_mode
    if detection_mode == 'auto':
        detection_mode = device_caps.recommended_detection
    
    logger.info(f"Motion detection mode: {detection_mode}")
    motion_detector = MotionDetector(mode=detection_mode, sensitivity=config.motion_sensitivity)
    motion_buffer = MotionBuffer(buffer_size=config.min_motion_frames)
    
    # Initialize recorder
    recorder = ClipRecorder(
        clips_dir=config.clips_dir,
        clip_duration=config.clip_duration
    )
    
    # Initialize OneDrive
    if config.onedrive_access_token and not config.onedrive_mock:
        onedrive_manager = OneDriveManager(
            access_token=config.onedrive_access_token,
            folder_path=config.onedrive_folder_path,
            retention_days=config.onedrive_retention_days
        )
    else:
        logger.info("Using mock OneDrive")
        onedrive_manager = MockOneDrive()
    
    # Initialize Firebase
    if config.firebase_credentials_json and not config.firebase_mock:
        try:
            notifications = FirebaseNotifications(config.firebase_credentials_json)
        except:
            logger.warning("Firebase init failed, using mock")
            notifications = MockFirebase()
    else:
        logger.info("Using mock Firebase")
        notifications = MockFirebase()
    
    # Start stream
    if config.wyze_mock:
        logger.info("Using mock RTSP stream")
        mock_stream = MockRTSPStream()
        # For demo purposes, return mock
    else:
        stream_handler = RTSPStreamHandler(config.wyze_rtsp_url)
        if stream_handler.start():
            stream_handler.set_frame_callback(process_frame)
        else:
            logger.error("Failed to start RTSP stream")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global stream_handler
    
    if stream_handler:
        stream_handler.stop()
    
    logger.info("ThinkCam stopped")


def process_frame(frame):
    """Process frame for motion detection"""
    global current_clip, last_motion_time
    
    if motion_detector is None or recorder is None:
        return
    
    # Detect motion
    motion_detected, confidence = motion_detector.detect(frame)
    
    # Buffer motion detections
    should_trigger, avg_confidence = motion_buffer.add(motion_detected, confidence)
    
    # Log event
    event = {
        'timestamp': datetime.now().isoformat(),
        'motion': motion_detected,
        'confidence': confidence,
        'buffered_trigger': should_trigger,
        'avg_confidence': avg_confidence
    }
    events_log.append(event)
    
    # Keep last 1000 events
    if len(events_log) > 1000:
        events_log.pop(0)
    
    # Trigger recording on sustained motion
    if should_trigger:
        if not recorder.recording:
            logger.info(f"🎬 Motion triggered! Confidence: {avg_confidence:.0%}")
            recorder.start_recording(frame.shape[1], frame.shape[0])
            last_motion_time = datetime.now()
        
        recorder.add_frame(frame)
    
    # Stop recording if no motion for a while
    elif recorder.recording:
        duration = recorder.get_buffer_duration()
        if duration >= config.clip_duration:
            logger.info(f"⏹️  Recording stopped. Duration: {duration:.1f}s")
            clip_path = recorder.stop_recording(metadata={'confidence': avg_confidence})
            
            if clip_path:
                current_clip = clip_path
                # Upload to OneDrive
                if onedrive_manager:
                    onedrive_manager.upload_clip(clip_path)
    
    else:
        recorder.add_frame(frame)


@app.get("/health")
async def health():
    """Health check"""
    return {
        'status': 'healthy',
        'device': device_caps.device_type,
        'stream': 'connected' if stream_handler and stream_handler.frame is not None else 'disconnected'
    }


@app.get("/api/device-info")
async def device_info():
    """Get device capabilities"""
    return {
        'device_type': device_caps.device_type,
        'cpu_cores': device_caps.cpu_cores,
        'ram_gb': device_caps.ram_gb,
        'has_gpu': device_caps.has_gpu,
        'is_arm': device_caps.is_arm,
        'recommended_detection': device_caps.recommended_detection,
        'max_streams': device_caps.max_streams,
    }


@app.get("/api/rtsp-url")
async def get_rtsp_url():
    """Get RTSP URL for live view"""
    return {
        'rtsp_url': config.wyze_rtsp_url,
        'mock': config.wyze_mock
    }


@app.get("/api/events")
async def get_events(limit: int = 50):
    """Get recent motion events"""
    return {
        'events': events_log[-limit:],
        'total': len(events_log)
    }


@app.get("/api/status")
async def get_status():
    """Get current status"""
    global current_clip, last_motion_time
    
    return {
        'timestamp': datetime.now().isoformat(),
        'recording': recorder.recording if recorder else False,
        'buffered_frames': recorder.get_frame_count() if recorder else 0,
        'last_clip': current_clip,
        'last_motion': last_motion_time.isoformat() if last_motion_time else None,
        'motion_detection_mode': device_caps.recommended_detection,
    }


def main():
    """Run server"""
    logger.info(f"🌐 Starting API server on {config.api_host}:{config.api_port}")
    
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        debug=config.api_debug,
        log_level=config.log_level.lower()
    )


if __name__ == '__main__':
    main()
