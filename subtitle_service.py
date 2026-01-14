"""
Subtitle service using Groq Whisper for perfect word-level timing
"""
import logging
import os
import tempfile
import subprocess
from groq import AsyncGroq
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)


class SubtitleService:
    """Handles subtitle generation with perfect word-level timing"""
    
    def __init__(self):
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    
    async def generate_srt_from_audio(self, video_path: str, language: str = "es") -> str:
        """
        Generate SRT with word-level timing using Groq Whisper
        
        Args:
            video_path: Path to video file
            language: Language code
        
        Returns:
            SRT content with 1-2 words per subtitle
        """
        try:
            logger.info(f"Generating word-level SRT with Groq Whisper: {video_path}")
            
            # Extract audio
            audio_path = video_path.replace('.mp4', '_audio.mp3')
            
            extract_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'libmp3lame',
                '-q:a', '2', audio_path, '-y'
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
            
            logger.info("Audio extracted")
            
            # Transcribe with Groq Whisper (word-level timestamps!)
            with open(audio_path, 'rb') as audio_file:
                transcription = await self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                    language=language,
                    timestamp_granularities=["word"]
                )
            
            # Clean up
            try:
                os.remove(audio_path)
            except:
                pass
            
            logger.info("Groq transcription completed with word-level timing")
            
            # Create SRT with 1-2 words per subtitle
            srt_content = self._create_perfect_srt(transcription)
            
            logger.info(f"Perfect SRT generated: {len(srt_content)} chars")
            return srt_content
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    def _create_perfect_srt(self, transcription) -> str:
        """
        Create perfect Instagram/TikTok style SRT
        1-2 words per line, smooth timing
        """
        try:
            words = transcription.words if hasattr(transcription, 'words') else []
            
            if not words:
                raise Exception("No word-level timestamps from Groq")
            
            srt_lines = []
            subtitle_index = 1
            
            i = 0
            while i < len(words):
                # Decide: 1 or 2 words?
                current_word = words[i]['word']
                
                # Use 1 word if: long word (>7 chars) or last word
                if len(current_word) > 7 or i == len(words) - 1:
                    chunk = [words[i]]
                    chunk_size = 1
                # Use 2 words if both are short
                elif i + 1 < len(words):
                    next_word = words[i + 1]['word']
                    if len(current_word) + len(next_word) <= 12:
                        chunk = [words[i], words[i + 1]]
                        chunk_size = 2
                    else:
                        chunk = [words[i]]
                        chunk_size = 1
                else:
                    chunk = [words[i]]
                    chunk_size = 1
                
                # Get timing from Groq
                start_time = chunk[0]['start']
                end_time = chunk[-1]['end']
                
                # Add small buffer for readability (min 0.5s display)
                duration = end_time - start_time
                if duration < 0.5:
                    end_time = start_time + 0.5
                
                # Format text (uppercase)
                text = ' '.join([w['word'].strip() for w in chunk]).upper()
                
                # Format times as SRT
                start_srt = self._format_srt_time(start_time)
                end_srt = self._format_srt_time(end_time)
                
                # Add SRT entry
                srt_lines.append(f"{subtitle_index}")
                srt_lines.append(f"{start_srt} --> {end_srt}")
                srt_lines.append(text)
                srt_lines.append("")
                
                subtitle_index += 1
                i += chunk_size
            
            return '\n'.join(srt_lines)
        
        except Exception as e:
            logger.error(f"Failed to create perfect SRT: {str(e)}")
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
        Add perfect subtitles to video using FFmpeg
        
        Args:
            video_data: Video file as bytes
            srt_content: Optional SRT content
        
        Returns:
            Video with perfect subtitles
        """
        try:
            logger.info(f"Adding perfect subtitles: {len(video_data)} bytes")
            
            # Create temp files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            # Generate SRT if needed
            if not srt_content:
                srt_content = await self.generate_srt_from_audio(video_path, language="es")
            
            # Write SRT
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(srt_content)
            
            logger.info(f"SRT written: {srt_path}")
            
            # Output path
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            # Perfect Instagram/TikTok style
            subtitle_style = (
                f"FontName=Arial Black,"
                f"FontSize=14,"
                f"Bold=1,"
                f"PrimaryColour=&H0000FFFF,"  # Yellow
                f"OutlineColour=&H00000000,"  # Black outline
                f"BorderStyle=1,"
                f"Outline=1,"  # Thin outline
                f"Shadow=0,"
                f"Alignment=2,"  # Bottom center
                f"MarginV=60"
            )
            
            logger.info("Adding perfect subtitles with FFmpeg...")
            
            # Add subtitles
            ffmpeg_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:a', 'copy',
                '-preset', 'fast',
                output_path,
                '-y'
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            logger.info("FFmpeg completed")
            
            # Read output
            with open(output_path, 'rb') as output_file:
                subtitled_video = output_file.read()
            
            logger.info(f"Perfect subtitles added: {len(subtitled_video)} bytes")
            
            # Clean up
            try:
                os.remove(video_path)
                os.remove(srt_path)
                os.remove(output_path)
            except:
                pass
            
            return subtitled_video
        
        except Exception as e:
            logger.error(f"Adding subtitles failed: {str(e)}")
            raise


def create_subtitle_service() -> SubtitleService:
    """Factory function"""
    return SubtitleService()
