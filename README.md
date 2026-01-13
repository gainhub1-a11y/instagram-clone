# 📱 Instagram Clone Bot

Automated bot that monitors a Telegram channel and publishes content to Instagram with translation from Italian to Spanish.

## 🎯 Features

- ✅ **Photo Posts**: Single photos with translated captions
- ✅ **Carousels**: Multiple photos (2-10) with translated captions
- ✅ **Reels**: Videos with subtitles and translated captions
- ✅ **Auto Translation**: DeepL + OpenAI for high-quality translations
- ✅ **Subtitle Generation**: FFmpeg + Whisper for automatic Spanish subtitles
- ✅ **Error Handling**: Automatic retries with exponential backoff

## 📋 Requirements

- Python 3.11+
- FFmpeg (for subtitle generation)
- Telegram Bot
- Upload-Post.com account
- API Keys: DeepL, OpenAI, HeyGen, CloudConvert

## 🚀 Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/instagram-clone.git
cd instagram-clone
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
SOURCE_CHANNEL_ID=-1003579454785
UPLOADPOST_API_TOKEN=your_uploadpost_token
UPLOADPOST_PROFILE=testgain
DEEPL_API_KEY=your_deepl_key
OPENAI_API_KEY=your_openai_key
HEYGEN_API_KEY=your_heygen_key
CLOUDCONVERT_API_KEY=your_cloudconvert_key
```

### 4. Run Locally

```bash
python main.py
```

## 🌐 Deploy to Railway

### 1. Create New Project

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `instagram-clone` repository

### 2. Configure Environment Variables

In Railway dashboard, go to **Variables** and add:

```
TELEGRAM_BOT_TOKEN=8346319915:AAHe5rAo1UwKnScQ_gH3shv9tT8uupIi6s4
SOURCE_CHANNEL_ID=-1003579454785
UPLOADPOST_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
UPLOADPOST_PROFILE=testgain
DEEPL_API_KEY=your_key
OPENAI_API_KEY=your_key
HEYGEN_API_KEY=your_key
CLOUDCONVERT_API_KEY=your_key
```

### 3. Deploy

Railway will automatically:
- Detect Python
- Install dependencies from `requirements.txt`
- Run `Procfile` command: `python main.py`

## 📊 How It Works

1. **Monitor**: Bot watches Telegram channel for new posts
2. **Download**: Downloads photos/videos from Telegram
3. **Process**:
   - Photos: Keep as-is
   - Videos: Convert to MP4 → Add Spanish subtitles
4. **Translate**: Caption IT → ES with DeepL + OpenAI
5. **Publish**: Upload to Instagram via Upload-Post API

## 🎨 Content Types

### Single Photo
```
Input: 1 photo + caption (Italian)
Output: Instagram post with translated caption
```

### Carousel
```
Input: 2-10 photos + caption (Italian)
Output: Instagram carousel with translated caption
```

### Reel
```
Input: Video + caption (Italian)
Output: Instagram reel with Spanish subtitles + translated caption
```

## ⚙️ Configuration

Edit `config.py` to customize:

- `HEYGEN_TIMEOUT`: Max wait time for video translation (default: 600s)
- `CAROUSEL_WAIT_TIMEOUT`: Wait time for carousel items (default: 30s)
- `SUBTITLE_FONT_SIZE`: Subtitle text size (default: 16)
- `CAPTION_MAX_LENGTH`: Max caption length (default: 2200)

## 🐛 Troubleshooting

### Bot not receiving messages
- Ensure bot is added as admin to Telegram channel
- Check `SOURCE_CHANNEL_ID` is correct (use @userinfobot)

### Upload-Post errors
- Verify `UPLOADPOST_API_TOKEN` is valid
- Check Instagram account is connected in Upload-Post dashboard
- Ensure `UPLOADPOST_PROFILE` matches your profile name

### FFmpeg errors
- Install FFmpeg: `apt-get install ffmpeg` (Railway does this automatically)
- Check video format is supported

## 📝 License

MIT

## 👨‍💻 Support

For issues, contact: gainhub1@gmail.com
