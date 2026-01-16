import logging
import aiohttp
from typing import List, Tuple
from config import UPLOADPOST_API_TOKEN, UPLOADPOST_PROFILE, UPLOADPOST_API_URL

logger = logging.getLogger(__name__)


class UploadPostService:
    
    def __init__(self):
        self.api_token = UPLOADPOST_API_TOKEN
        self.profile = UPLOADPOST_PROFILE
        self.api_url = UPLOADPOST_API_URL
    
    async def publish_photo(self, image_data: bytes, caption: str, filename: str = "photo.jpg") -> dict:
        """
        Publish a single photo to Instagram
        """
        try:
            logger.info(f"Publishing photo to Instagram: {filename}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('photos[]', image_data, filename=filename, content_type='image/jpeg')
                form.add_field('video', '')  # Empty video field required by API
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                async with session.post(self.api_url, data=form, headers=headers) as response:
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
        Publish carousel of ONLY photos to Instagram
        """
        try:
            logger.info(f"Publishing photo carousel to Instagram: {len(items_data)} photos")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                # Add all photos with photos[] field
                for idx, image_data in enumerate(items_data):
                    form.add_field('photos[]', image_data, filename=f'photo_{idx}.jpg', content_type='image/jpeg')
                
                # Empty video field required by Upload-Post API
                form.add_field('video', '')
                
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                async with session.post(self.api_url, data=form, headers=headers) as response:
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
        items: List of (data, type) where type is 'photo' or 'video'
        """
        try:
            logger.info(f"Publishing mixed carousel to Instagram: {len(items)} items")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                photo_count = 0
                video_count = 0
                
                # Add all items with appropriate field names
                for idx, (media_data, media_type) in enumerate(items):
                    if media_type == 'photo':
                        form.add_field('photos[]', media_data, filename=f'photo_{photo_count}.jpg', content_type='image/jpeg')
                        photo_count += 1
                    elif media_type == 'video':
                        form.add_field('videos[]', media_data, filename=f'video_{video_count}.mp4', content_type='video/mp4')
                        video_count += 1
                
                logger.info(f"Mixed carousel: {photo_count} photos, {video_count} videos")
                
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                async with session.post(self.api_url, data=form, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise Exception(f"Upload-Post API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                
                logger.info(f"Mixed carousel published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish mixed carousel: {str(e)}")
            raise
    
    async def publish_reel(self, video_data: bytes, caption: str, filename: str = "reel.mp4") -> dict:
        """
        Publish a video/reel to Instagram
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
                
                logger.info(f"Sending request to: {self.api_url}")
                
                async with session.post(self.api_url, data=form, headers=headers) as response:
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
