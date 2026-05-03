import json
import os
import sys
import shutil
import sqlite3
import tempfile

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "twikit_cookies.json")


def export_x_cookies():
    print("=" * 50)
    print("XUAT COOKIES X.COM TU CHROME")
    print("=" * 50)
    print()

    # Tim file cookies Chrome
    local_app = os.environ.get("LOCALAPPDATA", "")
    chrome_base = os.path.join(local_app, "Google", "Chrome", "User Data")
    profiles = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 8"]

    cookies_dict = {}

    for profile in profiles:
        chrome_cookies = os.path.join(chrome_base, profile, "Network", "Cookies")
        if not os.path.exists(chrome_cookies):
            continue

        print(f"Tim thay cookies tai: {profile}/Network/Cookies")

        # Copy file de tranh lock
        tmp = os.path.join(tempfile.gettempdir(), f"chrome_cookies_{profile.replace(' ', '_')}")
        try:
            shutil.copy2(chrome_cookies, tmp)
        except Exception as e:
            print(f"  Khong copy duoc (Chrome dang mo?): {e}")
            continue

        try:
            conn = sqlite3.connect(tmp)
            cursor = conn.cursor()
            # Chrome luu encrypted_value va value - value chi co khi khong ma hoa
            cursor.execute(
                "SELECT name, value, encrypted_value FROM cookies "
                "WHERE host_key LIKE '%.x.com' OR host_key LIKE '%.twitter.com'"
            )
            rows = cursor.fetchall()
            conn.close()

            for name, value, enc_value in rows:
                if value:
                    cookies_dict[name] = value

            print(f"  Doc duoc {len(rows)} cookies tu {profile}")
        except Exception as e:
            print(f"  Loi doc SQLite: {e}")
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    # Kiem tra cookies quan trong
    important = {"auth_token", "ct0", "twid"} & set(cookies_dict.keys())

    if important:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies_dict, f, indent=2)
        print(f"\nThanh cong! Tim thay: {', '.join(important)}")
        print(f"Luu tai: {OUTPUT_FILE}")
        print("\nBay gio chay: python tweet_forward_bot.py")
        return True

    # Neu khong tim duoc value (bi encrypted), thu browser_cookie3
    print("\nCookies bi ma hoa. Thu browser_cookie3 (can dong Chrome)...")
    try:
        import browser_cookie3
        cj = browser_cookie3.chrome(domain_name=".x.com")
        for cookie in cj:
            cookies_dict[cookie.name] = cookie.value
        try:
            cj2 = browser_cookie3.chrome(domain_name=".twitter.com")
            for cookie in cj2:
                cookies_dict[cookie.name] = cookie.value
        except:
            pass

        important = {"auth_token", "ct0", "twid"} & set(cookies_dict.keys())
        if important:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies_dict, f, indent=2)
            print(f"Thanh cong! Tim thay: {', '.join(important)}")
            print(f"Luu tai: {OUTPUT_FILE}")
            print("\nBay gio chay: python tweet_forward_bot.py")
            return True
    except Exception as e:
        print(f"browser_cookie3 loi: {e}")

    print("\nKhong tim duoc cookies dang nhap!")
    print("Hay:")
    print("  1. Dang nhap x.com tren Chrome")
    print("  2. DONG Chrome hoan toan")
    print("  3. Chay lai: python export_x_cookies.py")
    return False


if __name__ == "__main__":
    export_x_cookies()
