FROM python:3.11-slim

# Install FFmpeg and font utilities
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create fonts directory
RUN mkdir -p /usr/share/fonts/truetype/custom

# Download TOP Instagram/TikTok fonts from Google Fonts
RUN cd /tmp && \
    # 🔥 MOST POPULAR - Montserrat
    wget -q https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-SemiBold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf && \
    # 🎨 BOLD & IMPACTFUL
    wget -q https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf && \
    # 🎪 PLAYFUL & FUN
    wget -q https://github.com/google/fonts/raw/main/ofl/luckiestguy/LuckiestGuy-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/permanentmarker/PermanentMarker-Regular.ttf && \
    # 🚀 MODERN & CLEAN - Poppins
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf && \
    # 🚀 MODERN & CLEAN - Others
    wget -q https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf && \
    wget -q https://github.com/google/fonts/raw/main/apache/opensans/OpenSans-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf && \
    # 💫 STYLISH & UNIQUE
    wget -q https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/righteous/Righteous-Regular.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/raleway/Raleway-Bold.ttf && \
    # 🎯 TRENDING 2025
    wget -q https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf && \
    wget -q https://github.com/google/fonts/raw/main/ofl/outfit/Outfit-Bold.ttf && \
    # Install all fonts
    mv *.ttf /usr/share/fonts/truetype/custom/ 2>/dev/null || true && \
    fc-cache -f -v && \
    rm -rf /tmp/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the bot
CMD ["python", "main.py"]
