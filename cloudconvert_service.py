"""
CloudConvert service for video format conversion
"""
import logging
import asyncio
import cloudconvert
from config import CLOUDCONVERT_API_KEY

logger = logging.getLogger(__name__)


class CloudConvertService:
    """Handles video format conversion using CloudConvert"""
    
    def __init__(self):
        self.api = cloudconvert.Api(api_key=CLOUDCONVERT_API_KEY, sandbox=False)
    
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
            
            # Create job with conversion task
            job = self.api.jobs.create({
                'tasks': {
                    'import-video': {
                        'operation': 'import/upload'
                    },
                    'convert-video': {
                        'operation': 'convert',
                        'input': 'import-video',
                        'output_format': 'mp4',
                        'video_codec': 'x264',
                        'audio_codec': 'aac'
                    },
                    'export-video': {
                        'operation': 'export/url',
                        'input': 'convert-video'
                    }
                }
            })
            
            logger.info(f"CloudConvert job created: {job['id']}")
            
            # Upload file
            upload_task = [task for task in job['tasks'] if task['name'] == 'import-video'][0]
            self.api.tasks.upload(upload_task['id'], video_data, filename)
            
            logger.info("Video uploaded to CloudConvert")
            
            # Wait for completion
            job = self.api.jobs.wait(job['id'])
            
            # Get export task
            export_task = [task for task in job['tasks'] if task['name'] == 'export-video'][0]
            
            if export_task['status'] != 'finished':
                raise Exception(f"CloudConvert export failed: {export_task.get('message', 'Unknown error')}")
            
            # Download converted file
            file_url = export_task['result']['files'][0]['url']
            
            logger.info(f"Downloading converted video from: {file_url}")
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download converted video: {response.status}")
                    converted_data = await response.read()
            
            logger.info(f"Video converted successfully: {len(converted_data)} bytes")
            return converted_data
        
        except Exception as e:
            logger.error(f"CloudConvert conversion failed: {str(e)}")
            raise


def create_cloudconvert_service() -> CloudConvertService:
    """Factory function to create a CloudConvertService instance"""
    return CloudConvertService()
