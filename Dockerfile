FROM python:3.10-slim

# Install ffmpeg and clean up apt lists
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN mkdir -p /downloads
EXPOSE 5000
CMD ["python", "app.py"]

