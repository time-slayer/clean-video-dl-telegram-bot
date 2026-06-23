FROM python:3.14-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (needed for yt-dlp/ffmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code directory
COPY src/ ./src/

# Create downloads directory
RUN mkdir -p downloads

# Run the bot
CMD ["python", "-m", "src.main"]
