"""
Instagram Clone Bot - Main Application
Monitors Telegram channel and publishes content to Instagram
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from config import (
    TELEGRAM_BOT_TOKEN,
    SOURCE_CHANNEL_ID,
    LOG_LEVEL,
    validate_config
)
from error_handler import create_error_handler
from translation_service import create_translation_service
from heygen_service import create_heygen_service
from cloudconvert_service import create_cloudconvert_service
from subtitle_service import create_subtitle_service
from uploadpost_service import create_uploadpost_service
from content_processor import ContentProcessor

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL)
)
logger = logging.getLogger(__name__)


class InstagramCloneBot:
    """Main bot class that orchestrates all services"""
    
    def __init__(self):
        self.app = None
        self.content_processor = None
    
    def initialize_services(self):
        """Initialize all services"""
        logger.info("Initializing services...")
        
        # Validate configuration
        validate_config()
        
        # Initialize services
        error_handler = create_error_handler()
        translation_service = create_translation_service()
        heygen_service = create_heygen_service()
        cloudconvert_service = create_cloudconvert_service()
        subtitle_service = create_subtitle_service()
        uploadpost_service = create_uploadpost_service()
        
        # Initialize content processor
        self.content_processor = ContentProcessor(
            bot=self.app.bot,
            error_handler=error_handler,
            translation_service=translation_service,
            heygen_service=heygen_service,
            cloudconvert_service=cloudconvert_service,
            subtitle_service=subtitle_service,
            uploadpost_service=uploadpost_service
        )
        
        logger.info("Services initialized successfully")
    
    async def handle_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new posts in the monitored channel"""
        message = update.channel_post
        
        if not message:
            return
        
        # Check if message is from the source channel
        if message.chat_id != SOURCE_CHANNEL_ID:
            logger.debug(f"Ignoring message from channel {message.chat_id}")
            return
        
        logger.info(f"New message from source channel: {message.message_id}")
        
        try:
            await self.content_processor.process_message(message)
        except Exception as e:
            logger.error(f"Failed to process message {message.message_id}: {str(e)}")
    
    def run(self):
        """Start the bot"""
        try:
            logger.info("Starting Instagram Clone Bot...")
            
            # Create application
            self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Initialize services
            self.initialize_services()
            
            # Add handler for channel posts
            self.app.add_handler(
                MessageHandler(
                    filters.ChatType.CHANNEL & (
                        filters.PHOTO | 
                        filters.VIDEO
                    ),
                    self.handle_channel_post
                )
            )
            
            logger.info(f"Bot started. Monitoring channel: {SOURCE_CHANNEL_ID}")
            logger.info("Press Ctrl+C to stop")
            
            # Start polling
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
        
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {str(e)}")
            raise


def main():
    """Main entry point"""
    bot = InstagramCloneBot()
    bot.run()


if __name__ == '__main__':
    main()
