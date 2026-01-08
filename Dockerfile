# Python ka base version
FROM python:3.9-slim

# FFmpeg install karne ka magic command
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Kaam karne ki jagah
WORKDIR /app

# Requirements file copy karo aur install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karo
COPY . .

# App run karo (Gunicorn ke saath)
CMD ["gunicorn", "-b", "0.0.0.0:10000", "flask_app:app"]
