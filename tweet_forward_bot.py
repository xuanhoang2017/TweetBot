import sys
import os
import json
import html
import re
import logging
import asyncio
from datetime import datetime

# --- GHI ĐÈ STDOUT/STDERR SỚM NHẤT CÓ THỂ ---
if sys.stdout is None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.stdout = open(os.path.join(base_dir, "tweet_bot_output.log"), "a", encoding="utf-8")
    sys.stderr = open(os.path.join(base_dir, "tweet_bot_error.log"), "a", encoding="utf-8")
    IS_HIDDEN_ENV = True
else:
    sys.stdout.reconfigure(encoding='utf-8')
    IS_HIDDEN_ENV = False

from twikit import Client
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto

load_dotenv()

# Telegram
TWEET_BOT_TOKEN = os.getenv("TWEET_BOT_TOKEN")
TWEET_CHAT_ID = os.getenv("TWEET_CHAT_ID")

# X credentials
X_USERNAME = os.getenv("X_USERNAME")
X_EMAIL = os.getenv("X_EMAIL")
X_PASSWORD = os.getenv("X_PASSWORD")

# Validate env sớm
_missing = [k for k, v in {
    "TWEET_BOT_TOKEN": TWEET_BOT_TOKEN,
    "TWEET_CHAT_ID": TWEET_CHAT_ID,
}.items() if not v]
if _missing:
    print(f"LỖI: Thiếu biến môi trường: {', '.join(_missing)}")
    sys.exit(1)

TRACKED_ACCOUNTS = [
    "real_stevele",
]
CHECK_INTERVAL = 120
TELEGRAM_CAPTION_LIMIT = 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "tweet_state.json")
COOKIES_FILE = os.path.join(BASE_DIR, "twikit_cookies.json")
LOCK_FILE = os.path.join(BASE_DIR, "tweet_bot.lock")

# Logging
handlers = [logging.FileHandler(os.path.join(BASE_DIR, "tweet_bot.log"), encoding='utf-8')]
if not IS_HIDDEN_ENV:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=handlers
)
logger = logging.getLogger("TweetForwardBot")

# Tắt log httpx để không lộ bot token trong log file
logging.getLogger("httpx").setLevel(logging.WARNING)


# --- Single-instance guard ---
_lock_fh = None

def acquire_lock() -> bool:
    """Tạo lock file để chống chạy nhiều instance."""
    global _lock_fh
    try:
        import msvcrt
        _lock_fh = open(LOCK_FILE, 'w')
        msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_NBLCK, 1)
        _lock_fh.write(str(os.getpid()))
        _lock_fh.flush()
        return True
    except (OSError, IOError):
        logger.error("Bot đang chạy ở process khác. Thoát.")
        return False

def release_lock():
    global _lock_fh
    if _lock_fh:
        try:
            import msvcrt
            msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
            _lock_fh.close()
        except:
            pass
        try:
            os.remove(LOCK_FILE)
        except:
            pass


# --- State ---
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        logger.error(f"Lỗi lưu state: {e}")


# --- Telegram ---
async def send_tweet_to_telegram(bot: Bot, tweet) -> bool:
    """Gửi tweet qua Telegram. Trả về True nếu thành công."""
    screen_name = tweet.user.screen_name
    text = getattr(tweet, 'full_text', None) or tweet.text
    tweet_id = tweet.id
    tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"

    # 1. Unescape HTML entities từ Twitter API (vd: &amp; → &)
    text = html.unescape(text)
    # 2. Xoá link t.co ở cuối tweet (link media/preview thừa)
    text = re.sub(r'\s*https://t\.co/\w+\s*$', '', text).strip()
    # 3. Escape lại cho Telegram HTML parse_mode
    safe_text = html.escape(text)

    # Twikit cung cấp list media trong tweet.media
    photo_urls = []
    if tweet.media:
        for media in tweet.media:
            mtype = getattr(media, 'type', None)
            url = getattr(media, 'media_url', None) or getattr(media, 'media_url_https', None)
            if mtype == 'photo' and url:
                photo_urls.append(url)

    message = f"👤 <b>@{screen_name}</b>\n\n{safe_text}\n\n🔗 <a href=\"{tweet_url}\">Xem trên X</a>"

    try:
        if photo_urls:
            # Telegram caption limit = 1024 chars
            if len(message) <= TELEGRAM_CAPTION_LIMIT:
                caption = message
            else:
                # Caption quá dài: gửi ảnh trước, text sau
                caption = f"👤 <b>@{screen_name}</b> — <a href=\"{tweet_url}\">Xem trên X</a>"

            if len(photo_urls) == 1:
                await bot.send_photo(
                    chat_id=TWEET_CHAT_ID,
                    photo=photo_urls[0],
                    caption=caption,
                    parse_mode='HTML'
                )
            else:
                media_group = []
                for i, url in enumerate(photo_urls):
                    if i == 0:
                        media_group.append(InputMediaPhoto(media=url, caption=caption, parse_mode='HTML'))
                    else:
                        media_group.append(InputMediaPhoto(media=url))
                await bot.send_media_group(chat_id=TWEET_CHAT_ID, media=media_group)

            # Nếu caption bị cắt, gửi full text riêng
            if len(message) > TELEGRAM_CAPTION_LIMIT:
                await bot.send_message(
                    chat_id=TWEET_CHAT_ID,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
        else:
            await bot.send_message(
                chat_id=TWEET_CHAT_ID,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
        logger.info(f"Đã gửi tweet của @{screen_name} (ID: {tweet_id})")
        return True
    except Exception as e:
        logger.error(f"Lỗi gửi tin nhắn (ID: {tweet_id}): {e}")
        return False


# --- Main ---
async def main():
    # Single-instance guard
    if not acquire_lock():
        return

    try:
        logger.info("Khởi động bot...")
        bot = Bot(token=TWEET_BOT_TOKEN)
        client = Client('en-US')

        # Load cookies (ưu tiên cookies đã export từ Chrome)
        if os.path.exists(COOKIES_FILE):
            try:
                client.load_cookies(COOKIES_FILE)
                logger.info("Đã load cookies từ file.")
            except Exception as e:
                logger.error(f"Lỗi load cookies: {e}")
                logger.error("Hãy chạy: python export_x_cookies.py")
                return
        else:
            # Thử đăng nhập tự động (có thể bị Cloudflare chặn)
            try:
                logger.info("Đang đăng nhập bằng twikit...")
                await client.login(
                    auth_info_1=X_USERNAME,
                    auth_info_2=X_EMAIL,
                    password=X_PASSWORD
                )
                client.save_cookies(COOKIES_FILE)
                logger.info("Đăng nhập thành công và lưu cookies.")
            except Exception as e:
                logger.error(f"Đăng nhập thất bại: {e}")
                logger.error("Hãy đăng nhập X.com trên Chrome, đóng Chrome,")
                logger.error("rồi chạy: python import_x_cookies.py")
                return

        state = load_state()

        # Initialization
        if not state:
            logger.info("Lần đầu chạy: lấy danh sách tweet hiện tại để lưu ID.")
            for handle in TRACKED_ACCOUNTS:
                try:
                    user = await client.get_user_by_screen_name(handle)
                    tweets = await user.get_tweets('Tweets', count=5)
                    if tweets:
                        state[handle] = str(tweets[0].id)
                except Exception as e:
                    logger.error(f"Lỗi khi get info cho @{handle}: {e}")
                await asyncio.sleep(2)
            save_state(state)
            logger.info("Đã lưu state.")

        # Startup message (không crash nếu Telegram tạm lỗi)
        try:
            await bot.send_message(chat_id=TWEET_CHAT_ID, text="🤖 Bot đã khởi động!")
        except Exception as e:
            logger.warning(f"Không gửi được tin nhắn khởi động: {e}")

        # Vòng lặp quét
        while True:
            for handle in TRACKED_ACCOUNTS:
                try:
                    user = await client.get_user_by_screen_name(handle)
                    tweets = await user.get_tweets('Tweets', count=10)

                    if not tweets:
                        continue

                    last_seen_id = state.get(handle)
                    new_tweets = []
                    for tweet in tweets:
                        if last_seen_id is None or int(tweet.id) > int(last_seen_id):
                            is_rt = getattr(tweet, 'retweeted_tweet', None) is not None
                            if not is_rt:
                                new_tweets.append(tweet)

                    new_tweets.sort(key=lambda t: int(t.id))

                    for tweet in new_tweets:
                        sent = await send_tweet_to_telegram(bot, tweet)
                        if sent:
                            state[handle] = str(tweet.id)
                            save_state(state)
                        else:
                            # Dừng gửi tiếp để không nhảy state qua tweet bị fail
                            logger.warning(f"Dừng gửi cho @{handle}, sẽ thử lại vòng sau.")
                            break
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Lỗi quét feed cho @{handle}: {e}")

                await asyncio.sleep(3)
            await asyncio.sleep(CHECK_INTERVAL)
    finally:
        release_lock()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
