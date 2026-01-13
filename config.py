"""
Configuration file for Instagram Clone Bot
All sensitive data is loaded from environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# ============================
# TELEGRAM CONFIGURATION
# ============================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SOURCE_CHANNEL_ID = int(os.getenv('SOURCE_CHANNEL_ID', '0'))

# ============================
# UPLOAD-POST API
# ============================
UPLOADPOST_API_TOKEN = os.getenv('UPLOADPOST_API_TOKEN')
UPLOADPOST_PROFILE = os.getenv('UPLOADPOST_PROFILE', 'testgain')
UPLOADPOST_API_URL = 'https://api.upload-post.com/api/upload'

# ============================
# TRANSLATION SERVICES
# ============================
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# ============================
# VIDEO SERVICES
# ============================
HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY')

# ============================
# SERVICE TIMEOUTS & LIMITS
# ============================
HEYGEN_TIMEOUT = 600  # 10 minutes
HEYGEN_POLL_INTERVAL = 10  # seconds
CAPTION_MAX_LENGTH = 2200  # Instagram caption limit

# ============================
# CAROUSEL SETTINGS
# ============================
CAROUSEL_WAIT_TIMEOUT = 30  # seconds to wait for all carousel items
MAX_CAROUSEL_ITEMS = 10  # Instagram limit

# ============================
# SUBTITLE SETTINGS (FFmpeg)
# ============================
SUBTITLE_FONT = 'Arial'
SUBTITLE_FONT_SIZE = 16
SUBTITLE_COLOR = 'white'
SUBTITLE_POSITION = 'bottom'  # bottom, top, center
SUBTITLE_MAX_WORDS_PER_LINE = 2

# ============================
# ERROR HANDLING
# ============================
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# ============================
# LOGGING
# ============================
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


def validate_config():
    """Validate that all required environment variables are set"""
    required_vars = {
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'SOURCE_CHANNEL_ID': SOURCE_CHANNEL_ID,
        'UPLOADPOST_API_TOKEN': UPLOADPOST_API_TOKEN,
        'DEEPL_API_KEY': DEEPL_API_KEY,
        'OPENAI_API_KEY': OPENAI_API_KEY,
        'HEYGEN_API_KEY': HEYGEN_API_KEY,
        'CLOUDCONVERT_API_KEY': CLOUDCONVERT_API_KEY,
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set them in your .env file or Railway environment variables."
        )
    
    if SOURCE_CHANNEL_ID == 0:
        raise ValueError("SOURCE_CHANNEL_ID must be set to a valid channel ID (e.g., -1003579454785)")
    
    return True
