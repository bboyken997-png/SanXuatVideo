# YouTube Rewriter Telegram Bot

A Telegram bot that takes a YouTube link and produces a new video whose spoken
content differs from the original by ~40%: it downloads the video, transcribes the
speech, rewrites the script with an LLM, generates fresh narration (text-to-speech),
and re-edits the video (visual changes + burned-in subtitles + new audio).

> Use only with videos you own or are licensed to edit.

## Pipeline

```
YouTube URL
  -> yt-dlp            download video
  -> ffmpeg            extract audio
  -> faster-whisper    transcribe (local, free)
  -> LLM               rewrite transcript (~40% different)
  -> edge-tts          new narration (free, Vietnamese voices)
  -> ffmpeg            rebuild video (flip + color + subtitles + new audio)
  -> Telegram          send the new video back
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo apt-get install -y ffmpeg          # required
curl -fsSL https://deno.land/install.sh | sh   # JS runtime for yt-dlp (see below)
cp .env.example .env                    # then fill in the values
```

> **deno is required.** YouTube now serves video formats behind a JavaScript
> signature/n-sig challenge; yt-dlp solves it with a JS runtime (deno). Without it
> downloads return only image storyboards and fail. The bot passes
> `--remote-components ejs:github` so yt-dlp fetches the solver script on first use.
> Make sure `deno` is on `PATH` when running the bot.

### Required environment variables

- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather).
- One LLM provider for the rewrite step (or set `LLM_PROVIDER=none` for a low-quality
  offline fallback):
  - `LLM_PROVIDER=openai` + `OPENAI_API_KEY`
  - `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`

See `.env.example` for all options (Whisper model size, TTS voice, max duration,
allowed user IDs, target diff ratio).

## Run

```bash
python -m app.bot
```

Then message your bot a YouTube link.

## Deploy 24/7

See [DEPLOY.md](DEPLOY.md) for Docker Compose, systemd, and quick-run instructions.

## Notes

- The rewrite difference percentage is measured on the transcript text and reported in
  the reply caption.
- `MAX_DURATION_SECONDS` guards against very long videos (default 15 min).
- `ALLOWED_USER_IDS` restricts who can use the bot (recommended for public bots).

### YouTube bot check / cookies

YouTube often blocks downloads from servers/datacenter IPs with *"Sign in to confirm
you're not a bot"*. To fix this, provide cookies from a logged-in YouTube session:

- `YT_COOKIES_FILE=/path/to/cookies.txt` — export a Netscape-format `cookies.txt`
  using a browser extension (e.g. "Get cookies.txt") while logged into YouTube.
- or `YT_COOKIES_FROM_BROWSER=chrome` — read cookies straight from a local browser
  profile (only works if the bot host has that browser logged into YouTube).
