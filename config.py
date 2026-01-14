"""
Configuration file for the bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
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
SUBTITLE_COLOR = "#FFFF00"  # Yellow
SUBTITLE_POSITION = "bottom-center"
SUBTITLE_MAX_WORDS_PER_LINE = 2
```

---

## 📄 **2. requirements.txt - AGGIUNGI GROQ**
```
python-telegram-bot==20.7
python-dotenv==1.0.0
aiohttp==3.9.1
openai==1.12.0
groq>=0.4.0
deepl==1.16.1
requests==2.31.0
Pillow==10.2.0
