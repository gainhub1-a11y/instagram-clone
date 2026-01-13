"""
Subtitle service using FFmpeg to add subtitles to videos
"""
import logging
import os
import tempfile
import subprocess
from openai import AsyncOpenAI
from config import (
    OPENAI_API_KEY,
    SUBTITLE_FONT,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_COLOR,
    SUBTITLE_POSITION,
    SUBTITLE_MAX_WORDS_PER_LINE
)

logger = logging.getLogger(__name__)


class SubtitleService:
    """Handles subtitle generation and video embedding using FFmpeg"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    
    async def generate_srt_from_audio(self, video_path: str, language: str = "es") -> str:
        """
        Generate SRT subtitle file from video audio using OpenAI Whisper
        
        Args:
            video_path: Path to video file
            language: Language code (es for Spanish)
        
        Returns:
            SRT content as string
        """
        try:
            logger.info(f"Generating SRT subtitles from video: {video_path}")
            
            # Extract audio from video
            audio_path = video_path.replace('.mp4', '_audio.mp3')
            
            extract_cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                audio_path,
                '-y'  # Overwrite
            ]
            
            subprocess.run(extract_cmd, check=True, capture_output=True)
            logger.info("Audio extracted successfully")
            
            # Transcribe with Whisper
            with open(audio_path, 'rb') as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="srt",
                    language=language
                )
            
            # Clean up audio file
            os.remove(audio_path)
            
            logger.info(f"SRT generated successfully: {len(transcript)} characters")
            return transcript
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    async def add_subtitles_to_video(self, video_data: bytes, srt_content: str = None) -> bytes:
        """
        Add subtitles to video using FFmpeg
        
        Args:
            video_data: Video file as bytes
            srt_content: Optional SRT content (if None, will generate from audio)
        
        Returns:
            Video with subtitles as bytes
        """
        try:
            logger.info(f"Adding subtitles to video: {len(video_data)} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            # Generate SRT if not provided
            if not srt_content:
                srt_content = await self.generate_srt_from_audio(video_path, language="es")
            
            # Write SRT to file
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(srt_content)
            
            # Output path
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            # FFmpeg subtitle style (white text, no outline, uppercase, center-bottom)
            subtitle_style = (
                f"FontName={SUBTITLE_FONT},"
                f"FontSize={SUBTITLE_FONT_SIZE},"
                f"PrimaryColour=&HFFFFFF,"  # White
                f"Alignment=2"  # Bottom center
            )
            
            # Add subtitles with FFmpeg
            ffmpeg_cmd = [
                'ffmpeg', '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:a', 'copy',  # Copy audio without re-encoding
                output_path,
                '-y'
            ]
            
            logger.info("Running FFmpeg to add subtitles...")
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            # Read output video
            with open(output_path, 'rb') as output_file:
                subtitled_video = output_file.read()
            
            # Clean up temp files
            os.remove(video_path)
            os.remove(srt_path)
            os.remove(output_path)
            
            logger.info(f"Subtitles added successfully: {len(subtitled_video)} bytes")
            return subtitled_video
        
        except Exception as e:
            logger.error(f"Adding subtitles failed: {str(e)}")
            # Clean up on error
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(srt_path):
                    os.remove(srt_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
            except:
                pass
            raise


def create_subtitle_service() -> SubtitleService:
    """Factory function to create a SubtitleService instance"""
    return SubtitleService()
