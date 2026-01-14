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
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment variables")
        self.groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    
    async def generate_srt_from_audio(self, video_path: str, language: str = "es") -> str:
        """
        Generate SRT with word-level timing using Groq Whisper
        
        Args:
            video_path: Path to video file
            language: Language code (es for Spanish)
        
        Returns:
            SRT content with 1-2 words per subtitle
        """
        try:
            logger.info(f"Generating word-level SRT with Groq Whisper: {video_path}")
            
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
            
            # Transcribe with Groq Whisper (word-level timestamps!)
            with open(audio_path, 'rb') as audio_file:
                transcription = await self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                    language=language,
                    timestamp_granularities=["word"]
                )
            
            # Clean up audio file
            try:
                os.remove(audio_path)
            except:
                pass
            
            logger.info("Groq transcription completed with word-level timing")
            
            # Create SRT with 1-2 words per subtitle
            srt_content = self._create_perfect_srt(transcription)
            
            logger.info(f"Perfect SRT generated: {len(srt_content)} characters")
            return srt_content
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    def _create_perfect_srt(self, transcription) -> str:
        """
        Create perfect Instagram/TikTok style SRT
        1-2 words per line, smooth timing
        
        Args:
            transcription: Groq transcription with word-level timestamps
        
        Returns:
            SRT formatted string
        """
        try:
            # Get words with timestamps
            words = transcription.words if hasattr(transcription, 'words') else []
            
            if not words:
                logger.error("No word-level timestamps from Groq")
                raise Exception("No word-level timestamps available")
            
            logger.info(f"Processing {len(words)} words with timestamps")
            
            srt_lines = []
            subtitle_index = 1
            
            i = 0
            while i < len(words):
                # Get current word
                current_word = words[i]['word']
                
                # Decide: 1 or 2 words?
                # Use 1 word if: long word (>7 chars) or last word
                if len(current_word) > 7 or i == len(words) - 1:
                    chunk = [words[i]]
                    chunk_size = 1
                # Use 2 words if both are short
                elif i + 1 < len(words):
                    next_word = words[i + 1]['word']
                    # Combine if total length <= 12 characters
                    if len(current_word) + len(next_word) <= 12:
                        chunk = [words[i], words[i + 1]]
                        chunk_size = 2
                    else:
                        chunk = [words[i]]
                        chunk_size = 1
                else:
                    chunk = [words[i]]
                    chunk_size = 1
                
                # Get timing from Groq word timestamps
                start_time = chunk[0]['start']
                end_time = chunk[-1]['end']
                
                # Ensure minimum display time (0.5 seconds for readability)
                duration = end_time - start_time
                if duration < 0.5:
                    end_time = start_time + 0.5
                
                # Format text (uppercase for impact)
                text = ' '.join([w['word'].strip() for w in chunk]).upper()
                
                # Format times as SRT (HH:MM:SS,mmm)
                start_srt = self._format_srt_time(start_time)
                end_srt = self._format_srt_time(end_time)
                
                # Add SRT entry
                srt_lines.append(f"{subtitle_index}")
                srt_lines.append(f"{start_srt} --> {end_srt}")
                srt_lines.append(text)
                srt_lines.append("")  # Empty line separator
                
                subtitle_index += 1
                i += chunk_size
            
            logger.info(f"Created {subtitle_index - 1} subtitle entries")
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
            srt_content: Optional SRT content (if None, will generate from audio)
        
        Returns:
            Video with perfect subtitles as bytes
        """
        try:
            logger.info(f"Adding perfect subtitles to video: {len(video_data)} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            logger.info(f"Video written to temp file: {video_path}")
            
            # Generate SRT if not provided
            if not srt_content:
                logger.info("No SRT provided, generating from audio with Groq...")
                srt_content = await self.generate_srt_from_audio(video_path, language="es")
            
            # Write SRT to file
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write(srt_content)
            
            logger.info(f"SRT written to: {srt_path}")
            
            # Output path
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            # Perfect Instagram/TikTok subtitle style
            # Yellow text (14px), black outline (1px), bottom-center
            subtitle_style = (
                f"FontName=Arial Black,"
                f"FontSize=14,"
                f"Bold=1,"
                f"PrimaryColour=&H0000FFFF,"  # Yellow (BGR format: AABBGGRR)
                f"OutlineColour=&H00000000,"  # Black outline
                f"BorderStyle=1,"  # Outline only (no box)
                f"Outline=1,"  # 1px outline
                f"Shadow=0,"  # No shadow
                f"Alignment=2,"  # Bottom center
                f"MarginV=60"  # 60px from bottom
            )
            
            logger.info("Adding Instagram-style subtitles with FFmpeg...")
            
            # Add subtitles with FFmpeg
            ffmpeg_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-preset', 'fast',
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
            
            logger.info(f"Perfect subtitles added successfully: {len(subtitled_video)} bytes")
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
```

---

## ⚙️ **4. RAILWAY - AGGIUNGI VARIABILE**

1. **Railway Dashboard** → Progetto `instagram-clone`
2. **Variables** tab
3. **New Variable:**
```
   GROQ_API_KEY=gsk_tua_key_qui
```

---

## ✅ **DEPLOYMENT:**

1. **Carica su GitHub:**
   - `config.py` (aggiornato)
   - `requirements.txt` (aggiunto groq)
   - `subtitle_service.py` (versione Groq completa)

2. **Aggiungi variabile su Railway**

3. **Railway farà deploy automatico!**

---

## 📊 **COSA SUCCEDERÀ:**
```
Video → HeyGen traduzione → Groq Whisper (word-level timing) → SRT perfetto → FFmpeg → Instagram! 🎉
