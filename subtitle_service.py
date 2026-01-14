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
    
    async def generate_srt_from_audio(self, video_path: str, language: str = "es") -> str:
        """
        Generate SRT subtitle file from video audio using OpenAI Whisper
        With accurate timing for smooth Bookoly-style subtitles
        
        Args:
            video_path: Path to video file
            language: Language code (es for Spanish)
        
        Returns:
            SRT content as string with 1-2 words per subtitle
        """
        try:
            logger.info(f"Generating SRT subtitles from video: {video_path}")
            
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
            
            # Convert to SRT with accurate timing
            srt_content = self._create_smooth_bookoly_srt(transcript)
            
            logger.info(f"SRT generated successfully: {len(srt_content)} characters")
            return srt_content
        
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            raise
    
    def _create_smooth_bookoly_srt(self, transcript) -> str:
        """
        Create SRT with 1-2 words per subtitle with smooth timing
        Uses better timing distribution to avoid anticipation
        
        Args:
            transcript: Whisper verbose_json response
        
        Returns:
            SRT formatted string
        """
        try:
            segments = transcript.segments if hasattr(transcript, 'segments') else []
            srt_lines = []
            subtitle_index = 1
            
            for segment in segments:
                # Get segment timing and text
                start_time = segment['start']
                end_time = segment['end']
                text = segment['text'].strip()
                
                # Split text into words
                words = text.split()
                
                if not words:
                    continue
                
                # Calculate better timing distribution
                segment_duration = end_time - start_time
                
                # Estimate syllables for better timing (Spanish: ~1.5 syllables per word avg)
                total_syllables = sum(self._estimate_syllables(word) for word in words)
                time_per_syllable = segment_duration / total_syllables if total_syllables > 0 else 0
                
                # Create subtitle for each 1-2 words with smooth timing
                current_time = start_time
                i = 0
                
                while i < len(words):
                    # Decide chunk size (1-2 words)
                    # Use 1 word for long words, 2 for short words
                    if len(words[i]) > 7:
                        chunk_size = 1
                    elif i + 1 < len(words):
                        chunk_size = 2
                    else:
                        chunk_size = 1
                    
                    chunk_size = min(chunk_size, len(words) - i)
                    chunk = words[i:i+chunk_size]
                    
                    # Calculate duration based on syllables
                    chunk_syllables = sum(self._estimate_syllables(word) for word in chunk)
                    chunk_duration = chunk_syllables * time_per_syllable
                    
                    # Add small overlap for smoother transition (0.05s)
                    chunk_start = max(start_time, current_time - 0.05)
                    chunk_end = current_time + chunk_duration
                    
                    # Ensure we don't go past segment end
                    chunk_end = min(chunk_end, end_time)
                    
                    # Get text (uppercase for impact)
                    chunk_text = ' '.join(chunk).upper()
                    
                    # Format times as SRT
                    start_srt = self._format_srt_time(chunk_start)
                    end_srt = self._format_srt_time(chunk_end)
                    
                    # Add SRT entry
                    srt_lines.append(f"{subtitle_index}")
                    srt_lines.append(f"{start_srt} --> {end_srt}")
                    srt_lines.append(chunk_text)
                    srt_lines.append("")  # Empty line
                    
                    subtitle_index += 1
                    current_time = chunk_end
                    i += chunk_size
            
            return '\n'.join(srt_lines)
        
        except Exception as e:
            logger.error(f"Failed to create smooth Bookoly SRT: {str(e)}")
            raise
    
    def _estimate_syllables(self, word: str) -> int:
        """
        Estimate syllable count for Spanish word
        Simple heuristic: count vowels (a,e,i,o,u) as syllables
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
        
        # Minimum 1 syllable
        return max(1, syllable_count)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
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
            # Yellow text, small size (14), thin black outline (1px)
            subtitle_style = (
                f"FontName=Arial Black,"
                f"FontSize=14,"
                f"Bold=1,"
                f"PrimaryColour=&H0000FFFF,"  # Yellow (BGR: AABBGGRR)
                f"OutlineColour=&H00000000,"  # Black outline
                f"BorderStyle=1,"
                f"Outline=1,"  # Thin outline (1px)
                f"Shadow=0,"  # No shadow
                f"Alignment=2,"  # Bottom center
                f"MarginV=60"  # 60px from bottom
            )
            
            logger.info(f"Adding Bookoly-style yellow subtitles with FFmpeg...")
            
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
