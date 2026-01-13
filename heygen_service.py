"""
HeyGen service for video translation with subtitle generation
"""
import logging
import asyncio
import aiohttp
from config import HEYGEN_API_KEY, HEYGEN_TIMEOUT, HEYGEN_POLL_INTERVAL

logger = logging.getLogger(__name__)


class HeyGenService:
    """Handles video translation using HeyGen API"""
    
    def __init__(self):
        self.api_key = HEYGEN_API_KEY
        self.base_url = "https://api.heygen.com/v2/video_translate"
    
    async def translate_video(self, video_url: str) -> tuple[str, str]:
        """
        Translate video from Italian to Spanish using HeyGen
        
        Args:
            video_url: URL of the video to translate (must be publicly accessible)
        
        Returns:
            Tuple of (video_url, srt_content) - translated video URL and subtitle content
        """
        try:
            if not video_url.startswith('http'):
                raise ValueError(f"Invalid video URL: {video_url}")
            
            logger.info(f"Starting HeyGen video translation for URL: {video_url}")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-Api-Key": self.api_key,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                
                # Step 1: Submit translation request with subtitle generation
                payload = {
                    "video_url": video_url,
                    "output_language": "Spanish",
                    "speaker_num": 1,
                    "translate_audio_only": False
                }
                
                logger.info(f"Submitting HeyGen translation request")
                
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status not in [200, 202]:
                        error_text = await response.text()
                        raise Exception(f"HeyGen API error: {response.status} - {error_text}")
                    
                    result = await response.json()
                
                video_translate_id = result.get('data', {}).get('video_translate_id')
                
                if not video_translate_id:
                    raise Exception(f"No video_translate_id in response: {result}")
                
                logger.info(f"HeyGen translation started: {video_translate_id}")
                
                # Step 2: Poll for completion
                elapsed = 0
                status_check_url = f"{self.base_url}/{video_translate_id}"
                
                while elapsed < HEYGEN_TIMEOUT:
                    await asyncio.sleep(HEYGEN_POLL_INTERVAL)
                    elapsed += HEYGEN_POLL_INTERVAL
                    
                    async with session.get(status_check_url, headers=headers) as status_response:
                        if status_response.status != 200:
                            logger.warning(f"HeyGen status check failed: {status_response.status}")
                            continue
                        
                        status_result = await status_response.json()
                    
                    if not status_result.get('data'):
                        logger.warning(f"No data in status response")
                        continue
                    
                    data = status_result['data']
                    status = data.get('status')
                    video_url_result = data.get('url')
                    
                    logger.info(f"HeyGen status: {status} (elapsed: {elapsed}s) - URL present: {bool(video_url_result)}")
                    
                    if status in ['failed', 'error']:
                        error = data.get('error_message', 'Unknown error')
                        raise Exception(f"HeyGen translation failed: {error}")
                    
                    if status in ['completed', 'success'] and video_url_result:
                        logger.info(f"HeyGen translation completed with URL")
                        
                        # HeyGen provides the video, we'll generate SRT separately
                        # For now, return empty SRT (we'll use FFmpeg to generate it from audio)
                        srt_content = ""
                        
                        return video_url_result, srt_content
                
                raise TimeoutError(f"HeyGen translation timed out after {HEYGEN_TIMEOUT} seconds")
        
        except Exception as e:
            logger.error(f"HeyGen video translation failed: {str(e)}")
            raise


def create_heygen_service() -> HeyGenService:
    """Factory function to create a HeyGenService instance"""
    return HeyGenService()
