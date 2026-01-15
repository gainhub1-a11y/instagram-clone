FROM python:3.11-slim

# Install FFmpeg and font utilities
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    unzip \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create fonts directory
RUN mkdir -p /usr/share/fonts/truetype/google-fonts

# Download Google Fonts as ZIP and extract
RUN cd /tmp && \
    echo "=== DOWNLOADING FONT PACKS ===" && \
    wget -O montserrat.zip "https://fonts.google.com/download?family=Montserrat" && \
    wget -O bebasneue.zip "https://fonts.google.com/download?family=Bebas%20Neue" && \
    wget -O luckiestguy.zip "https://fonts.google.com/download?family=Luckiest%20Guy" && \
    wget -O bangers.zip "https://fonts.google.com/download?family=Bangers" && \
    wget -O anton.zip "https://fonts.google.com/download?family=Anton" && \
    wget -O poppins.zip "https://fonts.google.com/download?family=Poppins" && \
    wget -O roboto.zip "https://fonts.google.com/download?family=Roboto" && \
    wget -O oswald.zip "https://fonts.google.com/download?family=Oswald" && \
    wget -O permanentmarker.zip "https://fonts.google.com/download?family=Permanent%20Marker" && \
    wget -O pacifico.zip "https://fonts.google.com/download?family=Pacifico" && \
    wget -O inter.zip "https://fonts.google.com/download?family=Inter" && \
    wget -O outfit.zip "https://fonts.google.com/download?family=Outfit" && \
    echo "=== EXTRACTING FONTS ===" && \
    unzip -o "*.zip" -d /usr/share/fonts/truetype/google-fonts/ && \
    echo "=== FONTS EXTRACTED ===" && \
    find /usr/share/fonts/truetype/google-fonts/ -name "*.ttf" | wc -l && \
    echo "=== REBUILDING FONT CACHE ===" && \
    fc-cache -fv && \
    echo "=== AVAILABLE FONTS ===" && \
    fc-list : family | grep -i "luckiest\|montserrat\|bebas\|bangers\|anton" | sort | uniq && \
    echo "=== CLEANUP ===" && \
    rm -rf /tmp/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the bot
CMD ["python", "main.py"]
