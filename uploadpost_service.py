import logging
import aiohttp
from typing import List
from config import UPLOADPOST_API_TOKEN, UPLOADPOST_PROFILE, UPLOADPOST_API_URL

logger = logging.getLogger(__name__)


class UploadPostService:
    
    def __init__(self):
        self.api_token = UPLOADPOST_API_TOKEN
        self.profile = UPLOADPOST_PROFILE
        self.api_url = UPLOADPOST_API_URL
    
    async def publish_photo(self, image_data: bytes, caption: str, filename: str = "photo.jpg") -> dict:
        try:
            logger.info(f"Publishing photo to Instagram: {filename}")
            
            title = caption.split('.')[0].split('!')[0].split('?')[0][:100].strip()
            if not title:
                title = caption[:100].strip()
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('file', image_data, filename=filename, content_type='image/jpeg')
                form.add_field('title', title)
                form.add_field('caption', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': self.api_token
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
    
    async def publish_carousel(self, images_data: List[bytes], caption: str) -> dict:
        try:
            logger.info(f"Publishing carousel to Instagram: {len(images_data)} photos")
            
            title = caption.split('.')[0].split('!')[0].split('?')[0][:100].strip()
            if not title:
                title = caption[:100].strip()
            
            logger.info(f"Using title: {title}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                for idx, image_data in enumerate(images_data):
                    form.add_field(
                        f'file_{idx}',
                        image_data,
                        filename=f'photo_{idx}.jpg',
                        content_type='image/jpeg'
                    )
                
                form.add_field('title', title)
                form.add_field('caption', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                form.add_field('type', 'carousel')
                
                headers = {
                    'Authorization': self.api_token
                }
                
                async with session.post(self.api_url, data=form, headers=headers) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise Exception(f"Upload-Post API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                
                logger.info(f"Carousel published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish carousel: {str(e)}")
            raise
    
    async def publish_reel(self, video_data: bytes, caption: str, filename: str = "reel.mp4") -> dict:
        try:
            logger.info(f"Publishing reel to Instagram: {filename}")
            
            title = caption.split('.')[0].split('!')[0].split('?')[0][:100].strip()
            if not title:
                title = caption[:100].strip()
            
            logger.info(f"Using title: {title}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('video', video_data, filename=filename, content_type='video/mp4')
                form.add_field('title', title)
                form.add_field('caption', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': self.api_token
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
    
    async def publish_reel_from_url(self, video_url: str, caption: str) -> dict:
        try:
            logger.info(f"Publishing reel to Instagram from URL: {video_url}")
            
            title = caption.split('.')[0].split('!')[0].split('?')[0][:100].strip()
            if not title:
                title = caption[:100].strip()
            
            logger.info(f"Using title: {title}")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field('video_url', video_url)
                form.add_field('title', title)
                form.add_field('caption', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': self.api_token
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
                
                logger.info(f"Reel published successfully to Instagram from URL")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish reel from URL: {str(e)}")
            raise


def create_uploadpost_service() -> UploadPostService:
    return UploadPostService()
