# 🐦 Tweet Forward Bot

Bot Python tự động theo dõi các tài khoản X (Twitter) và forward tweet mới sang Telegram channel — kèm **full text** + **ảnh**.

## ✨ Tính năng

- 🔄 Tự động quét tweet mới mỗi 2 phút
- 📸 Gửi kèm ảnh (1 ảnh hoặc album nhiều ảnh)
- 📝 Lấy **full text** cho tweet dài (Premium/Blue)
- 🔒 Escape HTML an toàn cho Telegram
- 💾 Lưu state tránh gửi trùng, tự bắt kịp tweet miss khi restart
- 🪟 Chạy ngầm trên Windows (VBS + pythonw)
- 🔐 Single-instance lock chống chạy trùng

## 📋 Yêu cầu

- Python 3.10+
- Tài khoản X (Twitter) — dùng tài khoản phụ, **không dùng tài khoản chính**
- Telegram Bot Token + Chat ID

## 🚀 Cài đặt

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/TweetBot.git
cd TweetBot

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Cấu hình
cp .env.example .env
# Sửa .env với token và credentials của bạn

# 4. Patch twikit (BẮT BUỘC — xem mục bên dưới)

# 5. Lấy cookies X.com
python import_x_cookies.py

# 6. Chạy bot
python tweet_forward_bot.py
```

## 🍪 Lấy cookies X.com

Do Cloudflare chặn login tự động, bot dùng cookies từ Chrome:

1. Mở Chrome → vào **x.com** (đã đăng nhập)
2. Nhấn **F12** → tab **Application** → Cookies → `https://x.com`
3. Copy giá trị của: `auth_token`, `ct0`, `twid`
4. Chạy `python import_x_cookies.py` → paste từng giá trị

## 🔧 Patch twikit (bắt buộc)

Twikit 2.3.3 cần 2 patch thủ công do X thay đổi API:

### Patch 1: `transaction.py` (fix lỗi KEY_BYTE indices)

File: `site-packages/twikit/x_client_transaction/transaction.py`

Thêm regex mới để hỗ trợ webpack chunk format:
```python
CHUNK_NAME_REGEX = re.compile(r'"ondemand\.s"\s*:\s*"([a-f0-9]+)"')
```
Và fallback logic trong `get_indices()` method.

### Patch 2: `user.py` (fix KeyError)

File: `site-packages/twikit/user.py`

Đổi tất cả `legacy['key']` → `legacy.get('key', default)` trong `__init__`.

## 📁 Cấu trúc

```
TweetBot/
├── tweet_forward_bot.py     # Bot chính
├── import_x_cookies.py      # Tool nhập cookies từ DevTools
├── export_x_cookies.py      # Tool xuất cookies từ Chrome
├── scripts/
│   └── run_tweet_bot_hidden.vbs  # Chạy ngầm Windows
├── data/                    # Runtime data (gitignored)
│   ├── twikit_cookies.json
│   ├── tweet_state.json
│   └── tweet_bot.log
├── .env.example
├── requirements.txt
└── README.md
```

## 🪟 Tự động chạy khi Windows khởi động

1. Tạo shortcut đến `scripts/run_tweet_bot_hidden.vbs`
2. Copy shortcut vào `shell:startup`

## ⚠️ Lưu ý

- **Không dùng tài khoản X chính** — scraping vi phạm ToS, tài khoản có thể bị ban
- **Cookies sống vài tháng** — khi hết hạn chạy lại `import_x_cookies.py`
- **Không upgrade twikit** — `pip install --upgrade twikit` sẽ ghi đè patches
