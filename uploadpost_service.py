"""
Upload-Post service for publishing content to Instagram
"""
import logging
import aiohttp
from typing import List
from config import UPLOADPOST_API_TOKEN, UPLOADPOST_PROFILE, UPLOADPOST_API_URL

logger = logging.getLogger(__name__)


class UploadPostService:
    """Handles content publishing to Instagram via Upload-Post API"""
    
    def __init__(self):
        self.api_token = UPLOADPOST_API_TOKEN
        self.profile = UPLOADPOST_PROFILE
        self.api_url = UPLOADPOST_API_URL
    
    async def publish_photo(self, image_data: bytes, caption: str, filename: str = "photo.jpg") -> dict:
        """
        Publish single photo to Instagram
        
        Args:
            image_data: Image file as bytes
            caption: Caption text
            filename: Original filename
        
        Returns:
            API response dict
        """
        try:
            logger.info(f"Publishing photo to Instagram: {filename}")
            
            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                form = aiohttp.FormData()
                form.add_field('file', image_data, filename=filename, content_type='image/jpeg')
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
        """
        Publish carousel (multiple photos) to Instagram
        
        Args:
            images_data: List of image files as bytes
            caption: Caption text
        
        Returns:
            API response dict
        """
        try:
            logger.info(f"Publishing carousel to Instagram: {len(images_data)} photos")
            
            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                form = aiohttp.FormData()
                
                # Add all images
                for idx, image_data in enumerate(images_data):
                    form.add_field(
                        f'file_{idx}',
                        image_data,
                        filename=f'photo_{idx}.jpg',
                        content_type='image/jpeg'
                    )
                
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
        """
        Publish reel (video) to Instagram
        
        Args:
            video_data: Video file as bytes
            caption: Caption text
            filename: Original filename
        
        Returns:
            API response dict
        """
        try:
            logger.info(f"Publishing reel to Instagram: {filename}")
            
            # Extract first sentence as title (max 100 chars)
            # Split by common sentence endings
            title = caption.split('.')[0].split('!')[0].split('?')[0][:100].strip()
            if not title:
                title = caption[:100].strip()  # Fallback to first 100 chars
            
            logger.info(f"Using title: {title}")
            
            async with aiohttp.ClientSession() as session:
                # Prepare multipart form data
                form = aiohttp.FormData()
                form.add_field('file', video_data, filename=filename, content_type='video/mp4')
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
                
                logger.info(f"Reel published successfully to Instagram")
                return result
        
        except Exception as e:
            logger.error(f"Failed to publish reel: {str(e)}")
            raise


def create_uploadpost_service() -> UploadPostService:
    """Factory function to create an UploadPostService instance"""
    return UploadPostService()
