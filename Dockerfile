FROM python:3.11-slim

# Install FFmpeg and font utilities
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    wget \
    unzip \
    curl \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create fonts directory
RUN mkdir -p /usr/share/fonts/truetype/custom

# Download fonts from reliable CDN sources
RUN cd /tmp && \
    echo "=== DOWNLOADING FONTS FROM CDN ===" && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf" -o Montserrat.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf" -o BebasNeue.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/luckiestguy/LuckiestGuy-Regular.ttf" -o LuckiestGuy.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf" -o Bangers.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf" -o Anton.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf" -o Poppins-Bold.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf" -o Roboto-Bold.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald%5Bwght%5D.ttf" -o Oswald.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/permanentmarker/PermanentMarker-Regular.ttf" -o PermanentMarker.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/pacifico/Pacifico-Regular.ttf" -o Pacifico.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf" -o Inter.ttf && \
    curl -L "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit%5Bwght%5D.ttf" -o Outfit.ttf && \
    echo "=== FILES DOWNLOADED ===" && \
    ls -lah *.ttf && \
    mv *.ttf /usr/share/fonts/truetype/custom/ && \
    echo "=== FONTS MOVED ===" && \
    ls -lah /usr/share/fonts/truetype/custom/ && \
    fc-cache -fv && \
    echo "=== FONTS REGISTERED ===" && \
    fc-list : family | sort | uniq | head -30 && \
    rm -rf /tmp/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the bot
CMD ["python", "main.py"]
