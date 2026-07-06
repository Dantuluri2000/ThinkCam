"""
Recording module - Capture clips and encode with FFmpeg
"""
import cv2
import os
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ClipRecorder:
    """
    Records video clips when motion is detected
    Uses FFmpeg for efficient encoding
    """
    
    def __init__(self, clips_dir: str = './clips', clip_duration: int = 60):
        """
        Args:
            clips_dir: Directory to store clips
            clip_duration: Duration of each clip in seconds
        """
        self.clips_dir = clips_dir
        self.clip_duration = clip_duration
        self.recording = False
        self.frame_buffer = []
        self.fps = 30
        self.width = 0
        self.height = 0
        
        os.makedirs(clips_dir, exist_ok=True)
    
    def start_recording(self, width: int, height: int, fps: int = 30):
        """Start recording a clip"""
        self.recording = True
        self.frame_buffer = []
        self.width = width
        self.height = height
        self.fps = fps
        logger.info(f"📹 Recording started: {width}x{height} @ {fps} fps")
    
    def add_frame(self, frame):
        """Add frame to recording buffer"""
        if self.recording:
            self.frame_buffer.append(frame.copy())
    
    def stop_recording(self, metadata: dict = None) -> Optional[str]:
        """
        Stop recording and save clip
        
        Returns:
            Path to saved video file, or None if failed
        """
        if not self.recording:
            return None
        
        self.recording = False
        
        if not self.frame_buffer:
            logger.warning("No frames in buffer, not saving clip")
            return None
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        confidence = metadata.get('confidence', 0.0) if metadata else 0.0
        filename = f"motion_{timestamp}_{confidence:.2f}.mp4"
        filepath = os.path.join(self.clips_dir, filename)
        
        # Save clip using FFmpeg
        success = self._save_video(filepath)
        
        if success:
            logger.info(f"✅ Clip saved: {filepath}")
            return filepath
        else:
            logger.error(f"❌ Failed to save clip: {filepath}")
            return None
    
    def _save_video(self, output_path: str) -> bool:
        """Save frame buffer to video file using FFmpeg"""
        if not self.frame_buffer:
            return False
        
        try:
            # Create temporary raw video file
            temp_dir = os.path.dirname(output_path)
            temp_file = os.path.join(temp_dir, '.temp_raw.yuv')
            
            # Write frames to temporary raw file
            with open(temp_file, 'wb') as f:
                for frame in self.frame_buffer:
                    # Convert BGR to YUV420p (standard for ffmpeg)
                    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV_I420)
                    f.write(yuv.tobytes())
            
            # Use FFmpeg to encode
            cmd = [
                'ffmpeg',
                '-f', 'rawvideo',
                '-pix_fmt', 'yuv420p',
                '-s', f'{self.width}x{self.height}',
                '-r', str(self.fps),
                '-i', temp_file,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '23',
                output_path,
                '-y'  # Overwrite output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Cleanup temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if result.returncode == 0:
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error saving video: {e}")
            return False
    
    def get_frame_count(self) -> int:
        """Get number of frames in buffer"""
        return len(self.frame_buffer)
    
    def get_buffer_duration(self) -> float:
        """Get duration of buffered frames in seconds"""
        if self.fps == 0:
            return 0.0
        return len(self.frame_buffer) / self.fps
