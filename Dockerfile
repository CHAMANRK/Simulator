# Python ka base version
FROM python:3.9-slim

# FFmpeg install karna
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Kaam karne ki jagah
WORKDIR /app

# Requirements install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki code copy karna
COPY . .

# TIMEOUT BADHAYA (Yahan change kiya hai: --timeout 600)
CMD ["gunicorn", "--timeout", "600", "-b", "0.0.0.0:10000", "flask_app:app"]
