"""
Firebase notifications - Push alerts when motion detected
"""
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from typing import Optional

logger = logging.getLogger(__name__)


class FirebaseNotifications:
    """
    Sends push notifications via Firebase Cloud Messaging
    """
    
    def __init__(self, credentials_path: str):
        """
        Args:
            credentials_path: Path to Firebase service account JSON
        """
        self.credentials_path = credentials_path
        self.initialized = False
        
        self._init_firebase()
    
    def _init_firebase(self):
        """Initialize Firebase"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
            
            self.initialized = True
            logger.info("✅ Firebase initialized")
        except Exception as e:
            logger.warning(f"⚠️  Firebase init failed: {e}")
            self.initialized = False
    
    def send_motion_alert(self, device_token: str, camera_name: str, confidence: float) -> bool:
        """
        Send motion detection alert
        
        Args:
            device_token: Firebase device token
            camera_name: Camera name
            confidence: Detection confidence (0.0-1.0)
        
        Returns:
            True if sent successfully
        """
        if not self.initialized:
            logger.warning("Firebase not initialized, skipping notification")
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=f"Motion Detected - {camera_name}",
                    body=f"Confidence: {confidence:.0%}"
                ),
                data={
                    'camera': camera_name,
                    'confidence': f"{confidence:.2f}",
                    'action': 'VIEW_CLIP'
                },
                token=device_token,
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Alert sent: {response}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def send_error_alert(self, device_token: str, error_message: str) -> bool:
        """Send error notification"""
        if not self.initialized:
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="ThinkCam Error",
                    body=error_message
                ),
                token=device_token,
            )
            
            messaging.send(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")
            return False


class MockFirebase:
    """Mock Firebase for testing"""
    
    def __init__(self, credentials_path: str = None):
        logger.info("✅ [MOCK] Firebase initialized")
    
    def send_motion_alert(self, device_token: str, camera_name: str, confidence: float) -> bool:
        logger.info(f"📱 [MOCK] Alert: {camera_name} - {confidence:.0%}")
        return True
    
    def send_error_alert(self, device_token: str, error_message: str) -> bool:
        logger.error(f"🚨 [MOCK] Error: {error_message}")
        return True
