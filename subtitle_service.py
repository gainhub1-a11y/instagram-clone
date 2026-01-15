import logging
import os
import tempfile
import subprocess
from groq import AsyncGroq
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)


class SubtitleService:
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    
    async def generate_srt_from_audio(self, video_path: str, language: str = "es") -> str:
        try:
            logger.info(f"Generating word-by-word karaoke SRT with Groq Whisper: {video_path}")
            
            audio_path = video_path.replace('.mp4', '_audio.mp3')
            
            extract_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                audio_path,
                '-y'
            ]
            
            result = subprocess.run(extract_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg extract audio failed: {result.stderr}")
                raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
            
            logger.info("Audio extracted successfully")
            
            with open(audio_path, 'rb') as audio_file:
                transcription = await self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                    language=language,
                    timestamp_granularities=["word"]
                )
            
            try:
                os.remove(audio_path)
            except:
                pass
            
            logger.info("Groq transcription completed with word-level timing")
            
            srt_content = self._create_karaoke_srt(transcription)
            
            logger.info(f"Karaoke SRT generated: {len(srt_content)} characters")
            return srt_content
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    def _create_karaoke_srt(self, transcription) -> str:
        """
        Create karaoke-style subtitles - ONE WORD AT A TIME
        Each word appears exactly when it's spoken, then disappears
        """
        try:
            words = transcription.words if hasattr(transcription, 'words') else []
            
            if not words:
                logger.error("No word-level timestamps from Groq")
                raise Exception("No word-level timestamps available")
            
            logger.info(f"Creating karaoke subtitles for {len(words)} words")
            
            srt_lines = []
            
            for idx, word_info in enumerate(words):
                word = word_info['word'].strip().upper()
                start_time = word_info['start']
                end_time = word_info['end']
                
                # Ensure minimum duration of 0.3s per word for readability
                duration = end_time - start_time
                if duration < 0.3:
                    end_time = start_time + 0.3
                
                # Format SRT timestamps
                start_srt = self._format_srt_time(start_time)
                end_srt = self._format_srt_time(end_time)
                
                # Add to SRT - ONE WORD ONLY
                srt_lines.append(f"{idx + 1}")
                srt_lines.append(f"{start_srt} --> {end_srt}")
                srt_lines.append(word)
                srt_lines.append("")
            
            logger.info(f"Created {len(words)} karaoke subtitle entries (one per word)")
            return '\n'.join(srt_lines)
        
        except Exception as e:
            logger.error(f"Failed to create karaoke SRT: {str(e)}")
            raise
    
    def _format_srt_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    async def add_subtitles_to_video(self, video_data: bytes, srt_content: str = None) -> bytes:
        try:
            logger.info(f"Adding karaoke subtitles to video: {len(video_data)} bytes ({len(video_data)/1024/1024:.2f} MB)")
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            logger.info(f"Video written to temp file: {video_path}")
            
            if not srt_content:
                logger.info("No SRT provided, generating karaoke subtitles with Groq...")
                srt_content = await self.generate_srt_from_audio(video_path, language="es")
            
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(srt_content)
            
            logger.info(f"SRT written to: {srt_path}")
            
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            # Karaoke-style subtitles - ONE WORD, FONT 14, CENTERED
            subtitle_style = (
                f"FontName=Arial Black,"
                f"FontSize=14,"
                f"Bold=1,"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour=&H00000000,"
                f"BorderStyle=1,"
                f"Outline=3,"
                f"Shadow=0,"
                f"Alignment=2,"
                f"MarginV=100"
            )
            
            logger.info("Adding karaoke-style subtitles with aggressive compression...")
            
            ffmpeg_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:v', 'libx264',
                '-preset', 'slow',
                '-crf', '32',
                '-maxrate', '1.5M',
                '-bufsize', '1.5M',
                '-c:a', 'aac',
                '-b:a', '96k',
                output_path,
                '-y'
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg subtitle addition failed: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            logger.info("FFmpeg completed successfully")
            
            with open(output_path, 'rb') as output_file:
                subtitled_video = output_file.read()
            
            output_size_mb = len(subtitled_video) / 1024 / 1024
            logger.info(f"Subtitled video size: {len(subtitled_video)} bytes ({output_size_mb:.2f} MB)")
            
            if output_size_mb > 100:
                logger.warning(f"Video exceeds 100MB Instagram API limit! ({output_size_mb:.2f} MB)")
            
            try:
                os.remove(video_path)
                os.remove(srt_path)
                os.remove(output_path)
                logger.info("Temp files cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Cleanup warning: {cleanup_error}")
            
            logger.info(f"Karaoke subtitles added successfully: {len(subtitled_video)} bytes")
            return subtitled_video
        
        except Exception as e:
            logger.error(f"Adding subtitles failed: {str(e)}")
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
    return SubtitleService()
