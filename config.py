"""
Configuration file for the bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SOURCE_CHANNEL_ID = int(os.getenv('SOURCE_CHANNEL_ID', '-1003579454785'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003579454785'))

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Groq Configuration (for Whisper word-level timestamps)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# DeepL Configuration
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')

# CloudConvert Configuration
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

# HeyGen Configuration
HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')

# Upload-Post Configuration
UPLOADPOST_API_TOKEN = os.getenv('UPLOADPOST_API_TOKEN')
UPLOADPOST_PROFILE = os.getenv('UPLOADPOST_PROFILE')
UPLOADPOST_API_URL = os.getenv('UPLOADPOST_API_URL', 'https://app.upload-post.com/api/v2/media/create')

# Subtitle Configuration
SUBTITLE_FONT = "Arial Black"
SUBTITLE_FONT_SIZE = 14
SUBTITLE_COLOR = "#FFFF00"
SUBTITLE_POSITION = "bottom-center"
SUBTITLE_MAX_WORDS_PER_LINE = 2

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def validate_config():
    """
    Validate that all required environment variables are set
    """
    required_vars = {
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'GROQ_API_KEY': GROQ_API_KEY,
        'DEEPL_API_KEY': DEEPL_API_KEY,
        'CLOUDCONVERT_API_KEY': CLOUDCONVERT_API_KEY,
        'HEYGEN_API_KEY': HEYGEN_API_KEY,
        'UPLOADPOST_API_TOKEN': UPLOADPOST_API_TOKEN,
        'UPLOADPOST_PROFILE': UPLOADPOST_PROFILE,
    }
    
    missing = [var for var, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True
