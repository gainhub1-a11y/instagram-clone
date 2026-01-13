"""
Subtitle service using FFmpeg to add subtitles to videos
"""
import logging
import os
import re
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
        With word-level timing for karaoke effect
        
        Args:
            video_path: Path to video file
            language: Language code (es for Spanish)
        
        Returns:
            SRT content as string with 2-3 words per subtitle
        """
        try:
            logger.info(f"Generating word-level SRT subtitles from video: {video_path}")
            
            # Extract audio from video
            audio_path = video_path.replace('.mp4', '_audio.mp3')
            
            extract_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                audio_path,
                '-y'  # Overwrite
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg extract audio failed: {result.stderr}")
                raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
            
            logger.info("Audio extracted successfully")
            
            # Transcribe with Whisper (verbose JSON for word-level timing)
            with open(audio_path, 'rb') as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language=language,
                    timestamp_granularities=["word"]
                )
            
            # Clean up audio file
            try:
                os.remove(audio_path)
            except:
                pass
            
            logger.info(f"Whisper transcription completed with word-level timing")
            
            # Convert to SRT with 2-3 words per subtitle
            srt_content = self._create_bookoly_style_srt(transcript)
            
            logger.info(f"SRT generated successfully: {len(srt_content)} characters")
            return srt_content
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    def _create_bookoly_style_srt(self, transcript) -> str:
        """
        Create SRT with 2-3 words per subtitle (Bookoly style)
        
        Args:
            transcript: Whisper verbose_json response with word-level timing
        
        Returns:
            SRT formatted string
        """
        try:
            words = transcript.words
            srt_lines = []
            subtitle_index = 1
            
            # Group words into chunks of 2-3 words
            i = 0
            while i < len(words):
                # Take 2-3 words
                chunk_size = min(3, len(words) - i)
                chunk = words[i:i+chunk_size]
                
                if not chunk:
                    break
                
                # Get timing
                start_time = chunk[0]['start']
                end_time = chunk[-1]['end']
                
                # Get text (uppercase for impact)
                text = ' '.join([w['word'].strip() for w in chunk]).upper()
                
                # Format times as SRT (00:00:00,000)
                start_srt = self._format_srt_time(start_time)
                end_srt = self._format_srt_time(end_time)
                
                # Add SRT entry
                srt_lines.append(f"{subtitle_index}")
                srt_lines.append(f"{start_srt} --> {end_srt}")
                srt_lines.append(text)
                srt_lines.append("")  # Empty line
                
                subtitle_index += 1
                i += chunk_size
            
            return '\n'.join(srt_lines)
        
        except Exception as e:
            logger.error(f"Failed to create Bookoly-style SRT: {str(e)}")
            raise
    
    def _format_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def add_subtitles_to_video(self, video_data: bytes, srt_content: str = None) -> bytes:
        """
        Add subtitles to video using FFmpeg with Bookoly styling
        
        Args:
            video_data: Video file as bytes
            srt_content: Optional SRT content (if None, will generate from audio)
        
        Returns:
            Video with subtitles as bytes
        """
        try:
            logger.info(f"Adding Bookoly-style subtitles to video: {len(video_data)} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            logger.info(f"Video written to temp file: {video_path}")
            
            # Generate SRT if not provided
            if not srt_content:
                logger.info("No SRT provided, generating from audio...")
                srt_content = await self.generate_srt_from_audio(video_path, language="es")
            
            # Write SRT to file
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(srt_content)
            
            logger.info(f"SRT written to: {srt_path}")
            
            # Output path
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            # Bookoly-style subtitle formatting
            # White text, bold, large font, centered bottom
            subtitle_style = (
                f"FontName=Arial Black,"
                f"FontSize=28,"
                f"Bold=1,"
                f"PrimaryColour=&H00FFFFFF,"  # White
                f"OutlineColour=&H00000000,"  # Black outline
                f"BorderStyle=3,"  # Box background
                f"Outline=2,"  # Outline thickness
                f"Shadow=0,"
                f"Alignment=2,"  # Bottom center
                f"MarginV=80"  # 80px from bottom
            )
            
            logger.info(f"Adding Bookoly-style subtitles with FFmpeg...")
            
            # Add subtitles with FFmpeg
            ffmpeg_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-preset', 'fast',  # Faster encoding
                output_path,
                '-y'
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg subtitle addition failed: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            logger.info("FFmpeg completed successfully")
            
            # Read output video
            with open(output_path, 'rb') as output_file:
                subtitled_video = output_file.read()
            
            logger.info(f"Subtitled video read: {len(subtitled_video)} bytes")
            
            # Clean up temp files
            try:
                os.remove(video_path)
                os.remove(srt_path)
                os.remove(output_path)
                logger.info("Temp files cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Cleanup warning: {cleanup_error}")
            
            logger.info(f"Bookoly-style subtitles added successfully: {len(subtitled_video)} bytes")
            return subtitled_video
        
        except Exception as e:
            logger.error(f"Adding subtitles failed: {str(e)}")
            # Clean up on error
            try:
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)
                if 'srt_path' in locals() and os.path.exists(srt_path):
                    os.remove(srt_path)
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.remove(output_path)
            except:
                pass
            raise


def create_subtitle_service() -> SubtitleService:
    """Factory function to create a SubtitleService instance"""
    return SubtitleService()
