# Hướng dẫn deploy bot 24/7

Bot này dùng **long polling** (không cần domain hay mở port), nên chỉ cần một máy
Linux luôn bật (VPS rẻ là đủ). Dưới đây là 3 cách, chọn 1.

> Trước tiên cần: `TELEGRAM_BOT_TOKEN`, file `cookies.txt` của YouTube, và (tuỳ chọn)
> `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`. Xem `README.md` để biết cách lấy.

---

## Cách 1 — Docker Compose (khuyên dùng)

Yêu cầu: một VPS đã cài Docker + Docker Compose.

```bash
git clone https://github.com/bboyken997-png/SanXuatVideo
cd SanXuatVideo

# 1. Tạo cấu hình
cp .env.example .env
nano .env          # điền TELEGRAM_BOT_TOKEN, LLM key (nếu có)
#  -> đặt: YT_COOKIES_FILE=/secrets/cookies.txt

# 2. Đặt file cookies YouTube vào thư mục repo
#    (export bằng extension "Get cookies.txt LOCALLY")
cp /đường/dẫn/cookies.txt ./cookies.txt

# 3. Chạy nền, tự khởi động lại khi reboot
docker compose up -d --build

# Xem log
docker compose logs -f

# Cập nhật khi có code mới
git pull && docker compose up -d --build

# Dừng
docker compose down
```

`docker-compose.yml` đã mount sẵn `cookies.txt` vào `/secrets/cookies.txt` và lưu
cache model Whisper giữa các lần khởi động.

---

## Cách 2 — systemd (chạy trực tiếp trên VPS, không Docker)

```bash
sudo apt-get update && sudo apt-get install -y python3-venv ffmpeg git
git clone https://github.com/bboyken997-png/SanXuatVideo /opt/sanxuatvideo
cd /opt/sanxuatvideo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env     # điền token, key, YT_COOKIES_FILE=/opt/sanxuatvideo/cookies.txt
cp /đường/dẫn/cookies.txt /opt/sanxuatvideo/cookies.txt
```

Tạo service:

```bash
sudo tee /etc/systemd/system/sanxuatvideo.service >/dev/null <<'EOF'
[Unit]
Description=YouTube Rewriter Telegram Bot
After=network-online.target

[Service]
WorkingDirectory=/opt/sanxuatvideo
ExecStart=/opt/sanxuatvideo/.venv/bin/python -m app.bot
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now sanxuatvideo
sudo systemctl status sanxuatvideo      # kiểm tra
journalctl -u sanxuatvideo -f            # xem log
```

---

## Cách 3 — chạy nhanh để thử (không bền)

```bash
source .venv/bin/activate
nohup python -m app.bot > bot.log 2>&1 &
tail -f bot.log
```

Cách này tắt khi đóng terminal/reboot — chỉ để test.

---

## Lưu ý vận hành

- **Cookies hết hạn:** cookies YouTube có thể hết hạn sau một thời gian; nếu bot báo
  *"Sign in to confirm you're not a bot"*, export lại `cookies.txt` và restart.
- **RAM/CPU:** Whisper chạy CPU; với `WHISPER_MODEL=base` cần ~1–2GB RAM. Video dài
  sẽ tốn thời gian xử lý — chỉnh `MAX_DURATION_SECONDS` trong `.env`.
- **Bảo mật:** đặt `ALLOWED_USER_IDS` trong `.env` (lấy Telegram user ID của bạn từ
  [@userinfobot](https://t.me/userinfobot)) để chỉ bạn dùng được bot.
- **Bản quyền:** chỉ xử lý video bạn sở hữu hoặc được phép.
