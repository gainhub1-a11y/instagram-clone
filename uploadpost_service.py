import logging
import aiohttp
import subprocess
import tempfile
import os
from typing import List, Tuple
from pathlib import Path
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
    
    def extract_frames_from_video(self, video_data: bytes, num_frames: int = 3) -> List[bytes]:
        """
        Extract frames from video as JPEG images
        
        Args:
            video_data: Video data in bytes
            num_frames: Number of frames to extract (default: 3)
        
        Returns:
            List of frame data as bytes
        """
        frames = []
        temp_video = None
        temp_dir = None
        
        try:
            # Create temp directory for frames
            temp_dir = tempfile.mkdtemp()
            
            # Save video to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                tmp.write(video_data)
                temp_video = tmp.name
            
            logger.info(f"🎬 Extracting {num_frames} frames from video...")
            
            # Get video duration
            try:
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    temp_video
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
                duration = float(result.stdout.strip())
                logger.info(f"   Video duration: {duration:.2f}s")
            except Exception as e:
                logger.warning(f"   Could not get video duration: {e}, using default")
                duration = 10.0
            
            # Calculate timestamps for frames
            if num_frames == 1:
                timestamps = [duration / 2]
            else:
                # Skip first 10% and last 10% of video
                start = max(1.0, duration * 0.1)
                end = min(duration - 1.0, duration * 0.9)
                if end <= start:
                    end = start + 1
                interval = (end - start) / (num_frames - 1) if num_frames > 1 else 0
                timestamps = [start + (i * interval) for i in range(num_frames)]
            
            # Extract frames
            for i, timestamp in enumerate(timestamps):
                output_path = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
                
                cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', temp_video,
                    '-vframes', '1',
                    '-vf', 'scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2',
                    '-q:v', '2',
                    '-y',
                    output_path
                ]
                
                try:
                    subprocess.run(cmd, capture_output=True, check=True, timeout=15)
                    
                    # Read frame data
                    with open(output_path, 'rb') as f:
                        frame_data = f.read()
                        frames.append(frame_data)
                    
                    logger.info(f"   ✅ Frame {i+1}/{num_frames} @ {timestamp:.2f}s ({len(frame_data)} bytes)")
                    
                except subprocess.TimeoutExpired:
                    logger.error(f"   ❌ Timeout extracting frame {i+1}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"   ❌ Error extracting frame {i+1}: {e}")
            
            if not frames:
                raise Exception("Failed to extract any frames from video")
            
            logger.info(f"✅ Successfully extracted {len(frames)} frames from video")
            return frames
            
        except Exception as e:
            logger.error(f"❌ Failed to extract frames: {e}")
            raise
            
        finally:
            # Cleanup temp files
            try:
                if temp_video and os.path.exists(temp_video):
                    os.unlink(temp_video)
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
    
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
                
                url = f"{self.api_base_url}/api/upload_photos"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    
                    logger.info(f"Upload-Post response status: {response_status}")
                    logger.debug(f"Upload-Post response body: {response_text[:500]}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    # Try to parse JSON response
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        # Check for errors in response
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                        
                        logger.info(f"✅ Photo published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        # Response is not JSON
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        # If status is 200/201, consider it success
                        if response_status in [200, 201]:
                            logger.info(f"✅ Photo published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"❌ Failed to publish photo: {str(e)}")
            raise
    
    async def publish_carousel(self, items_data: List[bytes], caption: str) -> dict:
        """
        Publish carousel of ONLY photos to Instagram using upload_photos endpoint
        """
        try:
            logger.info(f"Publishing photo carousel to Instagram: {len(items_data)} photos")
            
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                
                # Add all photos
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
                    logger.debug(f"Upload-Post response body: {response_text[:500]}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    # Try to parse JSON response
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        # Check for errors in response
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                        
                        logger.info(f"✅ Photo carousel published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        # Response is not JSON
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        # If status is 200/201, consider it success
                        if response_status in [200, 201]:
                            logger.info(f"✅ Photo carousel published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"❌ Failed to publish photo carousel: {str(e)}")
            raise
    
    async def publish_mixed_carousel(self, items: List[Tuple[bytes, str]], caption: str) -> dict:
        """
        Publish carousel with MIXED content (photos + videos) to Instagram
        Videos are automatically converted to 3 frames each
        """
        try:
            logger.info(f"📦 Publishing mixed carousel to Instagram: {len(items)} items")
            
            # Process all items: keep photos, convert videos to frames
            all_photos = []
            video_count = 0
            photo_count = 0
            
            for idx, (data, media_type) in enumerate(items):
                if media_type == 'photo':
                    photo_count += 1
                    logger.info(f"   Item {idx+1}: 📸 Photo ({len(data)} bytes)")
                    all_photos.append(data)
                    
                elif media_type == 'video':
                    video_count += 1
                    logger.info(f"   Item {idx+1}: 🎬 Video ({len(data)} bytes) - converting to frames...")
                    
                    try:
                        # Extract 3 frames from video
                        frames = self.extract_frames_from_video(data, num_frames=3)
                        all_photos.extend(frames)
                        logger.info(f"   ✅ Video converted to {len(frames)} frames")
                    except Exception as e:
                        logger.error(f"   ❌ Failed to extract frames from video: {e}")
                        logger.warning(f"   ⚠️  Skipping this video")
                        continue
            
            if not all_photos:
                raise Exception("No photos found after processing mixed carousel")
            
            logger.info(f"📊 Final carousel composition:")
            logger.info(f"   • Original photos: {photo_count}")
            logger.info(f"   • Videos converted: {video_count}")
            logger.info(f"   • Total frames: {len(all_photos)}")
            
            # Check Instagram limit
            if len(all_photos) > 10:
                logger.warning(f"⚠️  Carousel has {len(all_photos)} items (max 10)")
                logger.warning(f"   Publishing only first 10 items")
                all_photos = all_photos[:10]
            
            # Publish as photo carousel
            return await self.publish_carousel(all_photos, caption)
        
        except Exception as e:
            logger.error(f"❌ Failed to publish mixed carousel: {str(e)}")
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
                
                url = f"{self.api_base_url}/api/upload"
                logger.info(f"Sending request to: {url}")
                
                async with session.post(url, data=form, headers=headers) as response:
                    response_status = response.status
                    response_text = await response.text()
                    
                    logger.info(f"Upload-Post response status: {response_status}")
                    logger.debug(f"Upload-Post response body: {response_text[:500]}")
                    
                    if response_status not in [200, 201]:
                        logger.error(f"Upload-Post error response: {response_text}")
                        raise Exception(f"Upload-Post API error: {response_status} - {response_text}")
                    
                    # Try to parse JSON response
                    try:
                        result = await response.json()
                        logger.info(f"Upload-Post JSON response: {result}")
                        
                        # Check for errors in response
                        if isinstance(result, dict):
                            if result.get('error') or result.get('status') == 'error':
                                error_msg = result.get('message', result.get('error', 'Unknown error'))
                                logger.error(f"Upload-Post returned error: {error_msg}")
                                raise Exception(f"Upload-Post returned error: {error_msg}")
                        
                        logger.info(f"✅ Reel published successfully to Instagram")
                        return result
                        
                    except (ValueError, aiohttp.ContentTypeError) as e:
                        # Response is not JSON
                        logger.warning(f"Non-JSON response from Upload-Post: {e}")
                        logger.info(f"Response text: {response_text}")
                        
                        # If status is 200/201, consider it success
                        if response_status in [200, 201]:
                            logger.info(f"✅ Reel published (non-JSON response)")
                            return {"status": "success", "message": "Published", "response": response_text}
                        else:
                            raise Exception(f"Invalid response format: {response_text}")
        
        except Exception as e:
            logger.error(f"❌ Failed to publish reel: {str(e)}")
            raise


def create_uploadpost_service() -> UploadPostService:
    return UploadPostService()
