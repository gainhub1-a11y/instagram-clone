import logging
import aiohttp
from typing import List, Tuple
from config import UPLOADPOST_API_TOKEN, UPLOADPOST_PROFILE, UPLOADPOST_API_URL

logger = logging.getLogger(__name__)


class UploadPostService:
    
    def __init__(self):
        self.api_token = UPLOADPOST_API_TOKEN
        self.profile = UPLOADPOST_PROFILE
        if '/api/upload' in UPLOADPOST_API_URL:
            self.api_base_url = UPLOADPOST_API_URL.rsplit('/api/upload', 1)[0]
        else:
            self.api_base_url = UPLOADPOST_API_URL.rstrip('/')
        
        logger.info(f"Upload-Post base URL: {self.api_base_url}")
    
    async def publish_photo(self, image_data: bytes, caption: str, filename: str = "photo.jpg") -> dict:
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
                
                url = f"{self.api_base_url}/api/upload_photos"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    
                    logger.info(f"Upload-Post response status: {response_status}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                            
                            instagram_result = result.get('results', {}).get('instagram', {})
                            if not instagram_result.get('success'):
                                error_msg = instagram_result.get('error', 'Unknown Instagram error')
                                logger.error(f"Instagram upload failed: {error_msg}")
                                raise Exception(f"Instagram upload failed: {error_msg}")
                        
                        logger.info(f"Photo published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        if response_status in [200, 201]:
                            logger.info(f"Photo published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"Failed to publish photo: {str(e)}")
            raise
    
    async def publish_carousel(self, items_data: List[bytes], caption: str) -> dict:
        try:
            logger.info(f"Publishing photo carousel to Instagram: {len(items_data)} photos")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                for idx, image_data in enumerate(items_data):
                    form.add_field('photos[]', image_data, filename=f'photo_{idx}.jpg', content_type='image/jpeg')
                
                form.add_field('title', caption[:100])
                form.add_field('description', caption)
                form.add_field('user', self.profile)
                form.add_field('platform[]', 'instagram')
                
                headers = {
                    'Authorization': f'Apikey {self.api_token}'
                }
                
                url = f"{self.api_base_url}/api/upload_photos"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    
                    logger.info(f"Upload-Post response status: {response_status}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                            
                            instagram_result = result.get('results', {}).get('instagram', {})
                            if not instagram_result.get('success'):
                                error_msg = instagram_result.get('error', 'Unknown Instagram error')
                                logger.error(f"Instagram upload failed: {error_msg}")
                                raise Exception(f"Instagram upload failed: {error_msg}")
                        
                        logger.info(f"Photo carousel published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        if response_status in [200, 201]:
                            logger.info(f"Photo carousel published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"Failed to publish photo carousel: {str(e)}")
            raise
    
    async def publish_video_carousel(self, videos_data: List[bytes], caption: str) -> dict:
        try:
            logger.info(f"Publishing video carousel to Instagram: {len(videos_data)} videos")
            
            results = []
            
            for idx, video_data in enumerate(videos_data):
                logger.info(f"Publishing video {idx+1}/{len(videos_data)} as individual reel...")
                try:
                    result = await self.publish_reel(video_data, caption, f"video_{idx}.mp4")
                    results.append(result)
                    logger.info(f"Video {idx+1}/{len(videos_data)} published successfully")
                except Exception as e:
                    logger.error(f"Failed to publish video {idx+1}/{len(videos_data)}: {e}")
                    results.append({"success": False, "error": str(e)})
            
            logger.info(f"Video carousel publishing completed: {len([r for r in results if r.get('success', True)])} successful")
            return {"success": True, "results": results}
        
        except Exception as e:
            logger.error(f"Failed to publish video carousel: {str(e)}")
            raise
    
    async def publish_mixed_carousel(self, items: List[Tuple[bytes, str]], caption: str) -> dict:
        try:
            logger.info(f"Publishing mixed carousel to Instagram: {len(items)} items")
            
            photos = []
            videos = []
            
            for idx, (data, media_type) in enumerate(items):
                if media_type == 'photo':
                    logger.info(f"Item {idx+1}: Photo ({len(data)} bytes)")
                    photos.append(data)
                elif media_type == 'video':
                    logger.info(f"Item {idx+1}: Video ({len(data)} bytes)")
                    videos.append(data)
            
            logger.info(f"Split carousel: {len(photos)} photos, {len(videos)} videos")
            
            results = {}
            
            if photos:
                logger.info(f"Publishing photo carousel: {len(photos)} photos")
                try:
                    photo_result = await self.publish_carousel(photos, caption)
                    results['photos'] = photo_result
                    logger.info(f"Photo carousel published successfully")
                except Exception as e:
                    logger.error(f"Failed to publish photo carousel: {e}")
                    results['photos'] = {"success": False, "error": str(e)}
            
            if videos:
                logger.info(f"Publishing video carousel: {len(videos)} videos as separate reels")
                try:
                    video_result = await self.publish_video_carousel(videos, caption)
                    results['videos'] = video_result
                    logger.info(f"Video carousel published successfully")
                except Exception as e:
                    logger.error(f"Failed to publish video carousel: {e}")
                    results['videos'] = {"success": False, "error": str(e)}
            
            logger.info(f"Mixed carousel published: photos={bool(photos)}, videos={bool(videos)}")
            return {"success": True, "results": results}
        
        except Exception as e:
            logger.error(f"Failed to publish mixed carousel: {str(e)}")
            raise
    
    async def publish_reel(self, video_data: bytes, caption: str, filename: str = "reel.mp4") -> dict:
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
                
                url = f"{self.api_base_url}/api/upload"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    
                    logger.info(f"Upload-Post response status: {response_status}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                            
                            instagram_result = result.get('results', {}).get('instagram', {})
                            if not instagram_result.get('success'):
                                error_msg = instagram_result.get('error', 'Unknown Instagram error')
                                logger.error(f"Instagram upload failed: {error_msg}")
                                raise Exception(f"Instagram upload failed: {error_msg}")
                        
                        logger.info(f"Reel published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        if response_status in [200, 201]:
                            logger.info(f"Reel published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"Failed to publish reel: {str(e)}")
            raise


def create_uploadpost_service() -> UploadPostService:
    return UploadPostService()
