import logging
import aiohttp
from typing import List, Tuple
from config import UPLOADPOST_API_TOKEN, UPLOADPOST_PROFILE, UPLOADPOST_API_URL

logger = logging.getLogger(__name__)


class UploadPostService:
    
    def __init__(self):
        self.api_token = UPLOADPOST_API_TOKEN
        self.profile = UPLOADPOST_PROFILE
        # Fix: Extract base URL correctly
        if '/api/upload' in UPLOADPOST_API_URL:
            self.api_base_url = UPLOADPOST_API_URL.rsplit('/api/upload', 1)[0]
        else:
            self.api_base_url = UPLOADPOST_API_URL.rstrip('/')
        
        logger.info(f"Upload-Post base URL: {self.api_base_url}")
    
    async def publish_photo(self, image_data: bytes, caption: str, filename: str = "photo.jpg") -> dict:
        """
        Publish a single photo to Instagram using upload_photos endpoint
        """
        try:
            logger.info(f"Publishing photo to Instagram: {filename}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('photos[]', image_data, filename=filename, content_type='image/jpeg')
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                # Use /api/upload_photos endpoint for photos
                url = f"{self.api_base_url}/api/upload_photos"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise Exception(f"Upload-Post API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                
                logger.info(f"Photo published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish photo: {str(e)}")
            raise
    
    async def publish_carousel(self, items_data: List[bytes], caption: str) -> dict:
        """
        Publish carousel of ONLY photos to Instagram using upload_photos endpoint
        """
        try:
            logger.info(f"Publishing photo carousel to Instagram: {len(items_data)} photos")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                # Add all photos with photos[] field
                for idx, image_data in enumerate(items_data):
                    form.add_field('photos[]', image_data, filename=f'photo_{idx}.jpg', content_type='image/jpeg')
                
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                # Use /api/upload_photos endpoint for photo carousels
                url = f"{self.api_base_url}/api/upload_photos"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise Exception(f"Upload-Post API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                
                logger.info(f"Photo carousel published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish photo carousel: {str(e)}")
            raise
    
    async def publish_mixed_carousel(self, items: List[Tuple[bytes, str]], caption: str) -> dict:
        """
        Publish carousel with MIXED content (photos + videos) to Instagram
        Note: Instagram API may not support mixed carousels via Upload-Post
        This will attempt to publish using photos endpoint
        """
        try:
            logger.info(f"Publishing mixed carousel to Instagram: {len(items)} items")
            
            # Check if we have videos
            has_videos = any(media_type == 'video' for _, media_type in items)
            
            if has_videos:
                logger.warning("Mixed carousel with videos - Instagram may not support this via Upload-Post API")
                logger.info("Converting to photo-only carousel by skipping videos")
                # Filter only photos
                photo_items = [data for data, media_type in items if media_type == 'photo']
                if photo_items:
                    return await self.publish_carousel(photo_items, caption)
                else:
                    raise Exception("No photos found in mixed carousel after filtering videos")
            else:
                # All photos
                photo_items = [data for data, _ in items]
                return await self.publish_carousel(photo_items, caption)
        
        except Exception as e:
            logger.error(f"Failed to publish mixed carousel: {str(e)}")
            raise
    
    async def publish_reel(self, video_data: bytes, caption: str, filename: str = "reel.mp4") -> dict:
        """
        Publish a video/reel to Instagram using upload endpoint
        """
        try:
            logger.info(f"Publishing reel to Instagram: {filename}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('video', video_data, filename=filename, content_type='video/mp4')
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                # Use /api/upload endpoint for videos
                url = f"{self.api_base_url}/api/upload"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    logger.info(f"Response status: {response_status}")
                    
                    if response_status not in [200, 201]:
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {error_text}")
                    
                    result = await response.json()
                    logger.info(f"Success response: {result}")
                
                logger.info(f"Reel published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish reel: {str(e)}")
            raise


def create_uploadpost_service() -> UploadPostService:
    return UploadPostService()
