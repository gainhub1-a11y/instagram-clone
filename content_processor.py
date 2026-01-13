"""
Content processor for Instagram - handles photos, carousels, and videos
"""
import logging
import asyncio
from typing import Dict, List
from telegram import Bot, Message
from io import BytesIO

from error_handler import ErrorHandler
from translation_service import TranslationService
from heygen_service import HeyGenService
from cloudconvert_service import CloudConvertService
from subtitle_service import SubtitleService
from uploadpost_service import UploadPostService
from config import CAROUSEL_WAIT_TIMEOUT, MAX_CAROUSEL_ITEMS, CAPTION_MAX_LENGTH

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Processes different types of content for Instagram"""
    
    def __init__(
        self,
        bot: Bot,
        error_handler: ErrorHandler,
        translation_service: TranslationService,
        heygen_service: HeyGenService,
        cloudconvert_service: CloudConvertService,
        subtitle_service: SubtitleService,
        uploadpost_service: UploadPostService
    ):
        self.bot = bot
        self.error_handler = error_handler
        self.translation = translation_service
        self.heygen = heygen_service
        self.cloudconvert = cloudconvert_service
        self.subtitle = subtitle_service
        self.uploadpost = uploadpost_service
        
        # Carousel management
        self.carousel_groups: Dict[str, List[bytes]] = {}
        self.carousel_captions: Dict[str, str] = {}
    
    async def process_message(self, message: Message):
        """Route message to appropriate processor"""
        try:
            # Check if part of media group (carousel)
            if message.media_group_id:
                await self.process_carousel_item(message)
            elif message.photo and message.caption:
                await self.process_photo_with_caption(message)
            elif message.video and message.caption:
                await self.process_video_with_caption(message)
            else:
                logger.warning(f"Unsupported message type: {message}")
        
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {str(e)}")
    
    async def process_photo_with_caption(self, message: Message):
        """Process single photo with caption"""
        logger.info(f"Processing single photo: {message.message_id}")
        
        try:
            # Download photo
            photo = message.photo[-1]  # Largest size
            file = await self.bot.get_file(photo.file_id)
            photo_data = await file.download_as_bytearray()
            
            logger.info(f"Photo downloaded: {len(photo_data)} bytes")
            
            # Translate caption
            translate_with_retry = self.error_handler.with_retry(
                module_name="CaptionTranslation",
                scenario="Translating photo caption",
                fallback_func=lambda: self.translation.translate_caption_openai_fallback(message.caption)
            )(self.translation.translate_caption)
            
            translated_caption = await translate_with_retry(message.caption)
            
            # Truncate if needed
            if len(translated_caption) > CAPTION_MAX_LENGTH:
                translated_caption = translated_caption[:CAPTION_MAX_LENGTH-3] + "..."
                logger.warning(f"Caption truncated to {CAPTION_MAX_LENGTH} characters")
            
            # Publish to Instagram
            publish_with_retry = self.error_handler.with_retry(
                module_name="InstagramPublish",
                scenario="Publishing photo to Instagram"
            )(self.uploadpost.publish_photo)
            
            await publish_with_retry(bytes(photo_data), translated_caption, "photo.jpg")
            
            logger.info("Photo published successfully to Instagram")
        
        except Exception as e:
            logger.error(f"Photo processing failed: {str(e)}")
            raise
    
    async def process_carousel_item(self, message: Message):
        """Collect carousel items and publish when complete"""
        media_group_id = message.media_group_id
        
        logger.info(f"Processing carousel item: group {media_group_id}")
        
        # Initialize group if new
        if media_group_id not in self.carousel_groups:
            self.carousel_groups[media_group_id] = []
            self.carousel_captions[media_group_id] = message.caption or ""
            logger.info(f"New carousel group started: {media_group_id}")
        
        # Download photo
        photo = message.photo[-1]
        file = await self.bot.get_file(photo.file_id)
        photo_data = await file.download_as_bytearray()
        
        # Add to group
        self.carousel_groups[media_group_id].append(bytes(photo_data))
        
        logger.info(f"Carousel item added: {len(self.carousel_groups[media_group_id])}/{MAX_CAROUSEL_ITEMS}")
        
        # Wait for more items
        await asyncio.sleep(CAROUSEL_WAIT_TIMEOUT)
        
        # Check if we should publish (no new items arrived)
        if len(self.carousel_groups[media_group_id]) <= MAX_CAROUSEL_ITEMS:
            await self.publish_carousel(media_group_id)
    
    async def publish_carousel(self, media_group_id: str):
        """Publish complete carousel to Instagram"""
        if media_group_id not in self.carousel_groups:
            return
        
        images = self.carousel_groups[media_group_id]
        caption = self.carousel_captions.get(media_group_id, "")
        
        logger.info(f"Publishing carousel: {len(images)} photos")
        
        try:
            # Translate caption
            if caption:
                translate_with_retry = self.error_handler.with_retry(
                    module_name="CaptionTranslation",
                    scenario="Translating carousel caption",
                    fallback_func=lambda: self.translation.translate_caption_openai_fallback(caption)
                )(self.translation.translate_caption)
                
                translated_caption = await translate_with_retry(caption)
            else:
                translated_caption = ""
            
            # Truncate if needed
            if len(translated_caption) > CAPTION_MAX_LENGTH:
                translated_caption = translated_caption[:CAPTION_MAX_LENGTH-3] + "..."
            
            # Publish to Instagram
            publish_with_retry = self.error_handler.with_retry(
                module_name="InstagramPublish",
                scenario="Publishing carousel to Instagram"
            )(self.uploadpost.publish_carousel)
            
            await publish_with_retry(images, translated_caption)
            
            logger.info("Carousel published successfully to Instagram")
            
            # Clean up
            del self.carousel_groups[media_group_id]
            if media_group_id in self.carousel_captions:
                del self.carousel_captions[media_group_id]
        
        except Exception as e:
            logger.error(f"Carousel publishing failed: {str(e)}")
            raise
    
    async def process_video_with_caption(self, message: Message):
        """Process video with caption (Reel)"""
        logger.info(f"Processing video: {message.message_id}")
        
        try:
            # Download video
            file = await self.bot.get_file(message.video.file_id)
            video_data = await file.download_as_bytearray()
            
            logger.info(f"Video downloaded: {len(video_data)} bytes")
            
            # Convert to MP4 and get URL from CloudConvert
            convert_with_retry = self.error_handler.with_retry(
                module_name="CloudConvert",
                scenario="Converting video to MP4 and getting URL"
            )(self.cloudconvert.convert_video_to_mp4_url)
            
            video_url = await convert_with_retry(bytes(video_data), "video")
            
            logger.info(f"Video converted and hosted at: {video_url}")
            
            # Translate video with HeyGen (includes audio translation and lip sync)
            translate_with_retry = self.error_handler.with_retry(
                module_name="HeyGenTranslation",
                scenario="Translating video with HeyGen"
            )(self.heygen.translate_video)
            
            translated_video_url, _ = await translate_with_retry(video_url)
            
            logger.info("Video translated with HeyGen (audio + lip sync)")
            
            # Download translated video
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(translated_video_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download translated video: {response.status}")
                    translated_video = await response.read()
            
            logger.info(f"Translated video downloaded: {len(translated_video)} bytes")
            
            # Add subtitles with FFmpeg
            subtitle_with_retry = self.error_handler.with_retry(
                module_name="SubtitleGeneration",
                scenario="Adding subtitles to translated video"
            )(self.subtitle.add_subtitles_to_video)
            
            final_video = await subtitle_with_retry(translated_video)
            
            logger.info(f"Subtitles added to video: {len(final_video)} bytes")
            
            # Translate caption
            translate_caption_with_retry = self.error_handler.with_retry(
                module_name="CaptionTranslation",
                scenario="Translating video caption",
                fallback_func=lambda: self.translation.translate_caption_openai_fallback(message.caption)
            )(self.translation.translate_caption)
            
            translated_caption = await translate_caption_with_retry(message.caption)
            
            # Truncate if needed
            if len(translated_caption) > CAPTION_MAX_LENGTH:
                translated_caption = translated_caption[:CAPTION_MAX_LENGTH-3] + "..."
            
            # Publish to Instagram
            publish_with_retry = self.error_handler.with_retry(
                module_name="InstagramPublish",
                scenario="Publishing reel to Instagram"
            )(self.uploadpost.publish_reel)
            
            await publish_with_retry(final_video, translated_caption, "reel.mp4")
            
            logger.info("Reel published successfully to Instagram")
        
        except Exception as e:
            logger.error(f"Video processing failed: {str(e)}")
            raise
