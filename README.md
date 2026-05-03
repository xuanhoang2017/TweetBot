# 🐦 Tweet Forward Bot

A Python bot that automatically monitors X (Twitter) accounts and forwards new tweets to a Telegram channel — with **full text** + **images**.

## ✨ Features

- 🔄 Auto-scans for new tweets every 2 minutes
- 📸 Sends photos (single or album) alongside tweet text
- 📝 Fetches **full text** for long tweets (Premium/Blue users)
- 🔒 HTML-safe escaping for Telegram parse mode
- 💾 State persistence to avoid duplicate sends & auto-catches missed tweets on restart
- 🪟 Runs silently on Windows (VBS + pythonw)
- 🔐 Single-instance lock to prevent duplicate processes

## 📋 Prerequisites

- Python 3.10+
- An X (Twitter) account — use a **throwaway account**, not your main one
- Telegram Bot Token + Chat ID

## 🚀 Setup

```bash
# 1. Clone the repo
git clone https://github.com/xuanhoang0299/TweetBot.git
cd TweetBot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your tokens and credentials

# 4. Patch twikit (REQUIRED — see section below)

# 5. Import X.com cookies
python import_x_cookies.py

# 6. Run the bot
python tweet_forward_bot.py
```

## 🍪 Getting X.com Cookies

Since Cloudflare blocks automated logins, the bot authenticates using browser cookies:

1. Open Chrome → go to **x.com** (must be logged in)
2. Press **F12** → go to **Application** tab → Cookies → `https://x.com`
3. Copy the values of: `auth_token`, `ct0`, `twid`
4. Run `python import_x_cookies.py` → paste each value when prompted

## 🔧 Patching twikit (Required)

twikit 2.3.3 requires 2 manual patches due to X API changes:

### Patch 1: `transaction.py` — Fixes `KEY_BYTE indices` error

**File:** `site-packages/twikit/x_client_transaction/transaction.py`

Add a new regex to support the modern webpack chunk format:
```python
CHUNK_NAME_REGEX = re.compile(r'"ondemand\.s"\s*:\s*"([a-f0-9]+)"')
```
And add fallback logic in the `get_indices()` method.

### Patch 2: `user.py` — Fixes `KeyError` crashes

**File:** `site-packages/twikit/user.py`

Replace all `legacy['key']` with `legacy.get('key', default)` in `User.__init__`.

## 📁 Project Structure

```
TweetBot/
├── tweet_forward_bot.py          # Main bot
├── import_x_cookies.py           # Import cookies from Chrome DevTools
├── export_x_cookies.py           # Export cookies directly from Chrome
├── scripts/
│   └── run_tweet_bot_hidden.vbs  # Silent Windows launcher
├── data/                         # Runtime data (gitignored)
│   ├── twikit_cookies.json
│   ├── tweet_state.json
│   └── tweet_bot.log
├── .env.example
├── requirements.txt
└── README.md
```

## 🪟 Auto-start on Windows Boot

1. Create a shortcut to `scripts/run_tweet_bot_hidden.vbs`
2. Place the shortcut in `shell:startup`

## ⚠️ Important Notes

- **Do NOT use your main X account** — scraping violates X's ToS and may result in a ban
- **Cookies last several months** — when they expire, re-run `import_x_cookies.py`
- **Do NOT upgrade twikit** — `pip install --upgrade twikit` will overwrite the required patches
