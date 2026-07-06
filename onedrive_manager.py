"""
OneDrive integration for cloud storage with 7-day rolling window
"""
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import Optional, List

logger = logging.getLogger(__name__)


class OneDriveManager:
    """
    Manages video clip uploads to OneDrive with automatic cleanup
    Maintains 7-day rolling window of clips
    """
    
    def __init__(self, access_token: str, folder_path: str = '/wyze-clips', retention_days: int = 7):
        """
        Args:
            access_token: OneDrive access token (from OAuth)
            folder_path: OneDrive folder path (e.g., '/wyze-clips')
            retention_days: Days to keep clips (auto-deletes older)
        """
        self.access_token = access_token
        self.folder_path = folder_path
        self.retention_days = retention_days
        self.graph_url = 'https://graph.microsoft.com/v1.0'
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def upload_clip(self, local_path: str) -> bool:
        """
        Upload a clip to OneDrive
        
        Returns:
            True if successful
        """
        if not os.path.exists(local_path):
            logger.error(f"❌ File not found: {local_path}")
            return False
        
        try:
            filename = os.path.basename(local_path)
            onedrive_path = f"{self.folder_path}/{filename}"
            
            # Ensure folder exists
            if not self._ensure_folder():
                logger.error("Failed to ensure OneDrive folder")
                return False
            
            # Upload file
            with open(local_path, 'rb') as f:
                file_size = os.path.getsize(local_path)
                logger.info(f"⬆️  Uploading: {filename} ({file_size / (1024*1024):.1f} MB)")
                
                upload_url = f"{self.graph_url}/me/drive/root:{onedrive_path}:/content"
                response = requests.put(
                    upload_url,
                    headers=self.headers,
                    data=f,
                    timeout=300  # 5 minute timeout for large files
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Uploaded: {filename}")
                    return True
                else:
                    logger.error(f"Upload failed: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
    
    def cleanup_old_clips(self) -> bool:
        """
        Delete clips older than retention period
        Maintains 7-day rolling window
        
        Returns:
            True if successful
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            # List all clips
            clips = self._list_clips()
            if not clips:
                logger.info("No clips to clean")
                return True
            
            deleted_count = 0
            for clip in clips:
                try:
                    # Extract date from filename (format: motion_YYYYMMDD_HHMMSS_conf.mp4)
                    filename = clip['name']
                    parts = filename.replace('motion_', '').replace('.mp4', '').split('_')
                    if len(parts) >= 2:
                        date_str = parts[0]
                        clip_date = datetime.strptime(date_str, '%Y%m%d')
                        
                        if clip_date < cutoff_date:
                            if self._delete_clip(clip['id']):
                                deleted_count += 1
                                logger.info(f"🗑️  Deleted old clip: {filename}")
                except Exception as e:
                    logger.warning(f"Error parsing/deleting clip {filename}: {e}")
            
            if deleted_count > 0:
                logger.info(f"✅ Cleaned up {deleted_count} old clips")
            
            return True
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
    
    def _ensure_folder(self) -> bool:
        """Ensure clip folder exists on OneDrive"""
        try:
            # Try to access folder
            url = f"{self.graph_url}/me/drive/root:{self.folder_path}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return True
            
            # Folder doesn't exist, create it
            parent_path = '/'.join(self.folder_path.split('/')[:-1]) or '/'
            folder_name = self.folder_path.split('/')[-1]
            
            url = f"{self.graph_url}/me/drive/root:{parent_path}:/children"
            data = {
                'name': folder_name,
                'folder': {},
                '@microsoft.graph.conflictBehavior': 'rename'
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                logger.info(f"📁 Created OneDrive folder: {self.folder_path}")
                return True
            else:
                logger.error(f"Failed to create folder: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error ensuring folder: {e}")
            return False
    
    def _list_clips(self) -> List[dict]:
        """List all clips in OneDrive folder"""
        try:
            url = f"{self.graph_url}/me/drive/root:{self.folder_path}:/children"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                items = response.json().get('value', [])
                # Filter to .mp4 files only
                return [item for item in items if item['name'].endswith('.mp4')]
            else:
                logger.warning(f"Failed to list clips: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error listing clips: {e}")
            return []
    
    def _delete_clip(self, item_id: str) -> bool:
        """Delete a clip by ID"""
        try:
            url = f"{self.graph_url}/me/drive/items/{item_id}"
            response = requests.delete(url, headers=self.headers)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error deleting clip: {e}")
            return False


class MockOneDrive:
    """Mock OneDrive for testing"""
    
    def __init__(self, local_folder: str = './onedrive_backup'):
        self.local_folder = local_folder
        os.makedirs(local_folder, exist_ok=True)
    
    def upload_clip(self, local_path: str) -> bool:
        """Mock upload - copies to local folder"""
        try:
            filename = os.path.basename(local_path)
            dest = os.path.join(self.local_folder, filename)
            import shutil
            shutil.copy2(local_path, dest)
            logger.info(f"✅ [MOCK] Uploaded: {filename}")
            return True
        except Exception as e:
            logger.error(f"Mock upload error: {e}")
            return False
    
    def cleanup_old_clips(self) -> bool:
        """Mock cleanup"""
        logger.info("✅ [MOCK] Cleaned up old clips")
        return True
