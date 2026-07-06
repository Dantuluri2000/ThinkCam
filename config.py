"""
Configuration management
Loads from .env file with sensible defaults
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv('.env.local', override=True)  # local secrets take priority


@dataclass
class Config:
    # Wyze API Credentials
    wyze_key_id: str = os.getenv('WYZE_KEY_ID', '')
    wyze_api_key: str = os.getenv('WYZE_API_KEY', '')
    wyze_email: str = os.getenv('WYZE_EMAIL', '')
    wyze_password: str = os.getenv('WYZE_PASSWORD', '')
    
    # Wyze Bridge / RTSP
    wyze_rtsp_url: str = os.getenv('WYZE_RTSP_URL', 'rtsp://localhost:8554/stream/front_door')
    wyze_mock: bool = os.getenv('WYZE_MOCK', 'false').lower() == 'true'
    
    # Motion Detection
    motion_sensitivity: float = float(os.getenv('MOTION_SENSITIVITY', '0.5'))
    min_motion_frames: int = int(os.getenv('MIN_MOTION_FRAMES', '3'))
    detection_mode: str = os.getenv('DETECTION_MODE', 'auto')  # auto, mediapipe_full, mediapipe_lite, framediff
    
    # Recording
    clips_dir: str = os.getenv('CLIPS_DIR', './clips')
    clip_duration: int = int(os.getenv('CLIP_DURATION', '60'))
    clip_trigger_threshold: float = float(os.getenv('CLIP_TRIGGER_THRESHOLD', '0.6'))
    
    # OneDrive
    onedrive_access_token: str = os.getenv('ONEDRIVE_ACCESS_TOKEN', '')
    onedrive_folder_path: str = os.getenv('ONEDRIVE_FOLDER_PATH', '/wyze-clips')
    onedrive_retention_days: int = int(os.getenv('RETENTION_DAYS', '7'))
    onedrive_mock: bool = os.getenv('ONEDRIVE_MOCK', 'false').lower() == 'true'
    
    # Firebase
    firebase_credentials_json: str = os.getenv('FIREBASE_CREDENTIALS_JSON', '')
    firebase_mock: bool = os.getenv('FIREBASE_MOCK', 'false').lower() == 'true'
    
    # API
    api_host: str = os.getenv('API_HOST', '0.0.0.0')
    api_port: int = int(os.getenv('API_PORT', '8000'))
    api_debug: bool = os.getenv('API_DEBUG', 'false').lower() == 'true'
    
    # Auth
    jwt_secret: str = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    jwt_algorithm: str = 'HS256'
    
    # Logging
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_file: str = os.getenv('LOG_FILE', 'logs/thinkcam.log')
    
    def validate(self) -> bool:
        """Validate critical config"""
        # Check Wyze credentials
        if self.wyze_key_id:
            print(f"✅ Wyze API Key loaded (ID: {self.wyze_key_id[:8]}...)")
        elif not self.wyze_mock:
            print("⚠️  Warning: Wyze API not configured, using mock mode")
            self.wyze_mock = True
        
        if not self.wyze_rtsp_url and not self.wyze_mock:
            print("⚠️  Warning: WYZE_RTSP_URL not set, using mock")
            self.wyze_mock = True
        
        return True


def get_config() -> Config:
    """Get config instance"""
    return Config()
