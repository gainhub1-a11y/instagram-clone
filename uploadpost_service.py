"""
Subtitle service using FFmpeg to add subtitles to videos
"""
import logging
import os
import re
import json
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
    
    async def generate_ass_from_audio(self, video_path: str, language: str = "es") -> str:
        """
        Generate ASS subtitle file with karaoke effect from video audio
        
        Args:
            video_path: Path to video file
            language: Language code (es for Spanish)
        
        Returns:
            ASS content as string with karaoke effect
        """
        try:
            logger.info(f"Generating ASS karaoke subtitles from video: {video_path}")
            
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
            
            # Transcribe with Whisper (verbose JSON for timing)
            with open(audio_path, 'rb') as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language=language
                )
            
            # Clean up audio file
            try:
                os.remove(audio_path)
            except:
                pass
            
            logger.info(f"Whisper transcription completed")
            
            # Convert to ASS with karaoke effect
            ass_content = self._create_karaoke_ass(transcript)
            
            logger.info(f"ASS karaoke generated successfully: {len(ass_content)} characters")
            return ass_content
        
        except Exception as e:
            logger.error(f"ASS generation failed: {str(e)}")
            raise
    
    def _create_karaoke_ass(self, transcript) -> str:
        """
        Create ASS file with karaoke effect
        All text in one line, words change color as spoken
        
        Args:
            transcript: Whisper verbose_json response
        
        Returns:
            ASS formatted string
        """
        try:
            segments = transcript.segments if hasattr(transcript, 'segments') else []
            
            # ASS Header
            ass_lines = [
                "[Script Info]",
                "Title: Karaoke Subtitles",
                "ScriptType: v4.00+",
                "WrapStyle: 0",
                "PlayResX: 384",
                "PlayResY: 288",
                "",
                "[V4+ Styles]",
                "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
                "Style: Default,Arial Black,14,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,1,0,2,10,10,60,1",
                "",
                "[Events]",
                "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
            ]
            
            # Process each segment
            for segment in segments:
                start_time = segment['start']
                end_time = segment['end']
                text = segment['text'].strip()
                
                # Split into words
                words = text.split()
                
                if not words:
                    continue
                
                # Calculate timing per word
                segment_duration = end_time - start_time
                
                # Estimate syllables for better timing
                total_syllables = sum(self._estimate_syllables(word) for word in words)
                time_per_syllable = segment_duration / total_syllables if total_syllables > 0 else 0
                
                # Build karaoke line
                karaoke_text = ""
                
                for word in words:
                    # Calculate duration for this word (in centiseconds for ASS)
                    word_syllables = self._estimate_syllables(word)
                    word_duration_seconds = word_syllables * time_per_syllable
                    word_duration_cs = int(word_duration_seconds * 100)  # centiseconds
                    
                    # Add karaoke tag {\kXX} where XX is duration in centiseconds
                    karaoke_text += f"{{\\k{word_duration_cs}}}{word.upper()} "
                
                # Format times for ASS (H:MM:SS.CC)
                start_ass = self._format_ass_time(start_time)
                end_ass = self._format_ass_time(end_time)
                
                # Add dialogue line
                ass_lines.append(
                    f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{karaoke_text.strip()}"
                )
            
            return '\n'.join(ass_lines)
        
        except Exception as e:
            logger.error(f"Failed to create karaoke ASS: {str(e)}")
            raise
    
    def _estimate_syllables(self, word: str) -> int:
        """
        Estimate syllable count for Spanish word
        """
        word = word.lower()
        vowels = 'aeiouáéíóú'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        return max(1, syllable_count)
    
    def _format_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    async def add_subtitles_to_video(self, video_data: bytes, subtitle_content: str = None) -> bytes:
        """
        Add karaoke subtitles to video using FFmpeg with ASS format
        
        Args:
            video_data: Video file as bytes
            subtitle_content: Optional ASS content (if None, will generate from audio)
        
        Returns:
            Video with karaoke subtitles as bytes
        """
        try:
            logger.info(f"Adding karaoke subtitles to video: {len(video_data)} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file:
                video_file.write(video_data)
                video_path = video_file.name
            
            logger.info(f"Video written to temp file: {video_path}")
            
            # Generate ASS if not provided
            if not subtitle_content:
                logger.info("No ASS provided, generating from audio...")
                subtitle_content = await self.generate_ass_from_audio(video_path, language="es")
            
            # Write ASS to file
            ass_path = video_path.replace('.mp4', '.ass')
            with open(ass_path, 'w', encoding='utf-8') as ass_file:
                ass_file.write(subtitle_content)
            
            logger.info(f"ASS written to: {ass_path}")
            
            # Output path
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            
            logger.info(f"Adding karaoke subtitles with FFmpeg...")
            
            # Add subtitles with FFmpeg using ASS filter
            ffmpeg_cmd = [
                '/usr/bin/ffmpeg', '-i', video_path,
                '-vf', f"ass={ass_path}",
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
                os.remove(ass_path)
                os.remove(output_path)
                logger.info("Temp files cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"Cleanup warning: {cleanup_error}")
            
            logger.info(f"Karaoke subtitles added successfully: {len(subtitled_video)} bytes")
            return subtitled_video
        
        except Exception as e:
            logger.error(f"Adding subtitles failed: {str(e)}")
            # Clean up on error
            try:
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)
                if 'ass_path' in locals() and os.path.exists(ass_path):
                    os.remove(ass_path)
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.remove(output_path)
            except:
                pass
            raise


def create_subtitle_service() -> SubtitleService:
    """Factory function to create a SubtitleService instance"""
    return SubtitleService()
