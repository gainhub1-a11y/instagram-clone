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

# Download fonts - CORRECT GitHub URLs!
RUN cd /tmp && \
    echo "=== DOWNLOADING FONTS ===" && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/montserrat/Montserrat-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/montserrat/Montserrat-SemiBold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/bebasneue/BebasNeue-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/anton/Anton-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/oswald/Oswald-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/luckiestguy/LuckiestGuy-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/bangers/Bangers-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/permanentmarker/PermanentMarker-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/poppins/Poppins-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/poppins/Poppins-SemiBold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/apache/roboto/Roboto-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/apache/roboto/Roboto-Black.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/apache/opensans/OpenSans-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/lato/Lato-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/pacifico/Pacifico-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/righteous/Righteous-Regular.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/raleway/Raleway-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/inter/Inter-Bold.ttf && \
    wget https://github.com/google/fonts/raw/refs/heads/main/ofl/outfit/Outfit-Bold.ttf && \
    echo "=== FONTS DOWNLOADED ===" && \
    ls -lah *.ttf && \
    echo "=== MOVING FONTS ===" && \
    mv *.ttf /usr/share/fonts/truetype/custom/ && \
    echo "=== FONTS IN DIRECTORY ===" && \
    ls -lah /usr/share/fonts/truetype/custom/ && \
    echo "=== REBUILDING FONT CACHE ===" && \
    fc-cache -fv && \
    echo "=== AVAILABLE FONTS ===" && \
    fc-list : family | sort | uniq && \
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
