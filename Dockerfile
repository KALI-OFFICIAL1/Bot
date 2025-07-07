# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all bot files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir pyrogram==2.0.106 tgcrypto==1.2.5

# Optional: create stats and log files if not exist
RUN touch stats.json deleted_log.txt edited_log.txt service_log.txt

# Set environment variables (optional fallback)
ENV API_ID="21546320"
ENV API_HASH="c16805d6f2393d35e7c49527daa317c7"
ENV BOT_TOKEN="7635808558:AAFTTOt7adAuS3DRGvlufuJWj5hWfIAobxE"
ENV LOG_CHAT_ID="-1002538785183"

# Run the bot
CMD ["python", "bot.py"]