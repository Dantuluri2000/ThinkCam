"""
RTSP stream handler for continuous video capture
"""
import cv2
import logging
import threading
import time
from typing import Optional, Callable
import numpy as np

logger = logging.getLogger(__name__)


class RTSPStreamHandler:
    """
    Handles continuous RTSP stream capture
    Supports callbacks for frame processing
    """
    
    def __init__(self, rtsp_url: str, buffer_size: int = 2):
        """
        Args:
            rtsp_url: RTSP stream URL
            buffer_size: Frame buffer size
        """
        self.rtsp_url = rtsp_url
        self.buffer_size = buffer_size
        self.is_running = False
        self.capture = None
        self.frame = None
        self.thread = None
        self.frame_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
    
    def start(self) -> bool:
        """Start capturing from RTSP stream"""
        try:
            # Set RTSP transport to TCP and timeout before opening
            cap = cv2.VideoCapture()
            cap.open(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            # Use TCP for RTSP (more reliable than UDP)
            self.capture = cv2.VideoCapture(
                self.rtsp_url + "?timeout=10000000",
                cv2.CAP_FFMPEG
            )
            cap.release()
            
            if not self.capture.isOpened():
                logger.error(f"❌ Failed to open RTSP stream: {self.rtsp_url}")
                return False
            
            # Get stream properties
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"✅ RTSP stream opened: {width}x{height} @ {fps} fps")
            
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting RTSP capture: {e}")
            return False
    
    def stop(self):
        """Stop capturing"""
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.capture:
            self.capture.release()
        
        logger.info("✅ RTSP capture stopped")
    
    def _capture_loop(self):
        """Main capture loop running in background thread"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_running:
            try:
                ret, frame = self.capture.read()
                
                if not ret:
                    consecutive_errors += 1
                    if consecutive_errors > max_consecutive_errors:
                        logger.error("Max consecutive read errors reached")
                        if self.error_callback:
                            self.error_callback("Stream read error")
                        break
                    time.sleep(0.1)
                    continue
                
                consecutive_errors = 0
                self.frame = frame
                
                # Call frame callback if registered
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        logger.warning(f"Frame callback error: {e}")
                
                time.sleep(0.01)  # Prevent CPU spinning
            
            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                consecutive_errors += 1
                if consecutive_errors > max_consecutive_errors:
                    if self.error_callback:
                        self.error_callback(str(e))
                    break
                time.sleep(1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get latest frame"""
        return self.frame
    
    def set_frame_callback(self, callback: Callable):
        """Register callback for frame processing"""
        self.frame_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Register callback for errors"""
        self.error_callback = callback


class MockRTSPStream:
    """
    Mock RTSP stream for testing (generates test frames)
    """
    
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.frame_count = 0
    
    def get_frame(self) -> np.ndarray:
        """Generate test frame"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Add some patterns
        cv2.putText(frame, f"Test Frame #{self.frame_count}", (50, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add motion simulation
        if self.frame_count % 30 < 15:
            cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), -1)
        
        self.frame_count += 1
        return frame
