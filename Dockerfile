FROM python:3.12-slim

# ffmpeg: audio extraction + video re-editing. curl/unzip: install deno below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# deno is the JavaScript runtime yt-dlp uses to solve YouTube's signature/n-sig
# challenge. Without it, only image/storyboard "formats" resolve.
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh
ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Cache directory for whisper models / temp work.
ENV HOME=/app
ENV XDG_CACHE_HOME=/app/.cache

CMD ["python", "-m", "app.bot"]
