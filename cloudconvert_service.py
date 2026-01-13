"""
CloudConvert service for video format conversion
"""
import logging
import asyncio
import aiohttp
from config import CLOUDCONVERT_API_KEY

logger = logging.getLogger(__name__)


class CloudConvertService:
    """Handles video format conversion using CloudConvert API directly"""
    
    def __init__(self):
        self.api_key = CLOUDCONVERT_API_KEY
        self.base_url = "https://api.cloudconvert.com/v2"
    
    async def convert_video_to_mp4(self, video_data: bytes, filename: str = "video") -> bytes:
        """
        Convert video to MP4 format with H.264 codec
        
        Args:
            video_data: Video file as bytes
            filename: Original filename (without extension)
        
        Returns:
            Converted video as bytes
        """
        try:
            logger.info(f"Starting CloudConvert video conversion: {len(video_data)} bytes")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Step 1: Create job
                job_payload = {
                    "tasks": {
                        "import-video": {
                            "operation": "import/upload"
                        },
                        "convert-video": {
                            "operation": "convert",
                            "input": "import-video",
                            "output_format": "mp4",
                            "video_codec": "x264",
                            "audio_codec": "aac"
                        },
                        "export-video": {
                            "operation": "export/url",
                            "input": "convert-video"
                        }
                    }
                }
                
                async with session.post(f"{self.base_url}/jobs", json=job_payload, headers=headers) as response:
                    if response.status != 201:
                        error = await response.text()
                        raise Exception(f"Failed to create CloudConvert job: {error}")
                    result = await response.json()
                
                job_id = result['data']['id']
                logger.info(f"CloudConvert job created: {job_id}")
                
                # Step 2: Upload file
                upload_task = [t for t in result['data']['tasks'] if t['name'] == 'import-video'][0]
                upload_url = upload_task['result']['form']['url']
                upload_params = upload_task['result']['form']['parameters']
                
                # Upload with multipart form
                form = aiohttp.FormData()
                for key, value in upload_params.items():
                    form.add_field(key, value)
                form.add_field('file', video_data, filename=f"{filename}.mp4")
                
                async with session.post(upload_url, data=form) as upload_response:
                    if upload_response.status not in [200, 201]:
                        error = await upload_response.text()
                        raise Exception(f"Failed to upload to CloudConvert: {error}")
                
                logger.info("Video uploaded to CloudConvert")
                
                # Step 3: Wait for completion
                while True:
                    await asyncio.sleep(5)
                    
                    async with session.get(f"{self.base_url}/jobs/{job_id}", headers=headers) as status_response:
                        if status_response.status != 200:
                            error = await status_response.text()
                            raise Exception(f"Failed to check job status: {error}")
                        status_result = await status_response.json()
                    
                    job_status = status_result['data']['status']
                    logger.info(f"CloudConvert job status: {job_status}")
                    
                    if job_status == 'finished':
                        break
                    elif job_status in ['error', 'failed']:
                        raise Exception(f"CloudConvert job failed: {status_result['data'].get('message', 'Unknown error')}")
                
                # Step 4: Download converted file
                export_task = [t for t in status_result['data']['tasks'] if t['name'] == 'export-video'][0]
                file_url = export_task['result']['files'][0]['url']
                
                logger.info(f"Downloading converted video from: {file_url}")
                
                async with session.get(file_url) as download_response:
                    if download_response.status != 200:
                        error = await download_response.text()
                        raise Exception(f"Failed to download converted video: {error}")
                    converted_data = await download_response.read()
                
                logger.info(f"Video converted successfully: {len(converted_data)} bytes")
                return converted_data
        
        except Exception as e:
            logger.error(f"CloudConvert conversion failed: {str(e)}")
            raise
    
    async def convert_video_to_mp4_url(self, video_data: bytes, filename: str = "video") -> str:
        """
        Convert video to MP4 and return CloudConvert URL (valid for 24h)
        
        Args:
            video_data: Video file as bytes
            filename: Original filename
        
        Returns:
            Public URL of converted video
        """
        try:
            logger.info(f"Converting video and getting URL: {len(video_data)} bytes")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Create job
                job_payload = {
                    "tasks": {
                        "import-video": {
                            "operation": "import/upload"
                        },
                        "convert-video": {
                            "operation": "convert",
                            "input": "import-video",
                            "output_format": "mp4",
                            "video_codec": "x264",
                            "audio_codec": "aac"
                        },
                        "export-video": {
                            "operation": "export/url",
                            "input": "convert-video"
                        }
                    }
                }
                
                async with session.post(f"{self.base_url}/jobs", json=job_payload, headers=headers) as response:
                    if response.status != 201:
                        error = await response.text()
                        raise Exception(f"Failed to create CloudConvert job: {error}")
                    result = await response.json()
                
                job_id = result['data']['id']
                
                # Upload file
                upload_task = [t for t in result['data']['tasks'] if t['name'] == 'import-video'][0]
                upload_url = upload_task['result']['form']['url']
                upload_params = upload_task['result']['form']['parameters']
                
                form = aiohttp.FormData()
                for key, value in upload_params.items():
                    form.add_field(key, value)
                form.add_field('file', video_data, filename=f"{filename}.mp4")
                
                async with session.post(upload_url, data=form) as upload_response:
                    if upload_response.status not in [200, 201]:
                        error = await upload_response.text()
                        raise Exception(f"Failed to upload: {error}")
                
                logger.info("Video uploaded to CloudConvert")
                
                # Wait for completion
                while True:
                    await asyncio.sleep(5)
                    
                    async with session.get(f"{self.base_url}/jobs/{job_id}", headers=headers) as status_response:
                        if status_response.status != 200:
                            raise Exception("Failed to check job status")
                        status_result = await status_response.json()
                    
                    job_status = status_result['data']['status']
                    logger.info(f"CloudConvert job status: {job_status}")
                    
                    if job_status == 'finished':
                        break
                    elif job_status in ['error', 'failed']:
                        raise Exception(f"CloudConvert job failed")
                
                # Get URL
                export_task = [t for t in status_result['data']['tasks'] if t['name'] == 'export-video'][0]
                file_url = export_task['result']['files'][0]['url']
                
                logger.info(f"Video URL ready (valid 24h): {file_url}")
                return file_url
        
        except Exception as e:
            logger.error(f"CloudConvert URL generation failed: {str(e)}")
            raise


def create_cloudconvert_service() -> CloudConvertService:
    """Factory function to create a CloudConvertService instance"""
    return CloudConvertService()
