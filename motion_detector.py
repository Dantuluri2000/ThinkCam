"""
Motion detection module with MediaPipe and fallback frame-diff
Auto-selects best detection method based on device capabilities
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class MotionDetector:
    """
    Flexible motion detection supporting:
    - MediaPipe Pose (person detection, full)
    - MediaPipe Lite (optimized for mobile)
    - Frame difference (low CPU fallback)
    """
    
    def __init__(self, mode: str = 'auto', sensitivity: float = 0.5):
        """
        Args:
            mode: 'mediapipe_full', 'mediapipe_lite', 'framediff', or 'auto'
            sensitivity: 0.0 (most alerts) to 1.0 (least alerts)
        """
        self.mode = mode
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self.prev_frame = None
        self.mediapipe = None
        
        self._init_detector()
    
    def _init_detector(self):
        """Initialize appropriate detector based on mode"""
        if self.mode in ['mediapipe_full', 'mediapipe_lite', 'auto']:
            self._init_mediapipe()
    
    def _init_mediapipe(self):
        """Initialize MediaPipe detector"""
        try:
            import mediapipe as mp
            mp_pose = mp.solutions.pose
            
            self.mediapipe = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0 if self.mode == 'mediapipe_lite' else 1,
                smooth_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            logger.info(f"✅ MediaPipe initialized ({self.mode})")
        except Exception as e:
            logger.warning(f"⚠️  MediaPipe init failed: {e}. Falling back to frame-diff.")
            self.mode = 'framediff'
            self.mediapipe = None
    
    def detect(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect motion in frame
        
        Returns:
            (motion_detected: bool, confidence: float)
        """
        if frame is None or frame.size == 0:
            return False, 0.0
        
        if self.mediapipe and self.mode.startswith('mediapipe'):
            return self._detect_mediapipe(frame)
        else:
            return self._detect_framediff(frame)
    
    def _detect_mediapipe(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect person/pose using MediaPipe
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mediapipe.process(rgb_frame)
            
            if results.pose_landmarks:
                # Person detected - return high confidence
                confidence = 0.9
                motion_detected = confidence > (1.0 - self.sensitivity)
                return motion_detected, confidence
            else:
                # No person detected
                return False, 0.0
        
        except Exception as e:
            logger.warning(f"MediaPipe detection error: {e}")
            return False, 0.0
    
    def _detect_framediff(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detect motion using frame-to-frame difference
        Low CPU fallback method
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return False, 0.0
        
        # Compute frame difference
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        
        # Threshold the difference
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Dilate to fill gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # Calculate motion percentage
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        motion_percentage = motion_pixels / total_pixels
        
        # Convert to confidence (0.0-1.0)
        confidence = min(1.0, motion_percentage * 10)
        
        # Threshold based on sensitivity
        threshold = 1.0 - self.sensitivity  # Higher sensitivity = lower threshold
        motion_detected = confidence > threshold
        
        self.prev_frame = gray
        
        return motion_detected, confidence
    
    def reset(self):
        """Reset detector state"""
        self.prev_frame = None


class MotionBuffer:
    """
    Buffers motion detections to reduce false positives
    Only triggers on sustained motion
    """
    
    def __init__(self, buffer_size: int = 3, trigger_threshold: int = 2):
        """
        Args:
            buffer_size: Number of frames to buffer
            trigger_threshold: How many detections needed to trigger
        """
        self.buffer_size = buffer_size
        self.trigger_threshold = trigger_threshold
        self.motion_buffer = []
        self.confidence_buffer = []
    
    def add(self, motion_detected: bool, confidence: float) -> Tuple[bool, float]:
        """
        Add detection to buffer
        
        Returns:
            (should_trigger: bool, avg_confidence: float)
        """
        self.motion_buffer.append(motion_detected)
        self.confidence_buffer.append(confidence)
        
        # Keep buffer size fixed
        if len(self.motion_buffer) > self.buffer_size:
            self.motion_buffer.pop(0)
            self.confidence_buffer.pop(0)
        
        # Check if enough motion detections in buffer
        motion_count = sum(self.motion_buffer)
        should_trigger = motion_count >= self.trigger_threshold
        
        avg_confidence = np.mean(self.confidence_buffer) if self.confidence_buffer else 0.0
        
        return should_trigger, avg_confidence
    
    def reset(self):
        """Reset buffer"""
        self.motion_buffer = []
        self.confidence_buffer = []
