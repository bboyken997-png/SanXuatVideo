FROM python:3.12-slim

# ffmpeg is required for audio extraction and video re-editing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Cache directory for whisper models / temp work.
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache

CMD ["python", "-m", "app.bot"]
