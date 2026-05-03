import json
import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "twikit_cookies.json")

print("=" * 55)
print("  NHAP COOKIES X.COM BANG TAY")
print("=" * 55)
print()
print("Huong dan lay cookies tu Chrome DevTools:")
print("-" * 55)
print("1. Mo Chrome, vao x.com (da dang nhap)")
print("2. Nhan F12 (mo DevTools)")
print("3. Chon tab 'Application' (hoac 'Storage')")
print("4. Ben trai, bam vao: Cookies > https://x.com")
print("5. Tim 3 dong sau va copy VALUE cua tung dong:")
print("   - auth_token")
print("   - ct0")
print("   - twid")
print("-" * 55)
print()

auth_token = input("Paste gia tri auth_token: ").strip()
ct0 = input("Paste gia tri ct0       : ").strip()
twid = input("Paste gia tri twid      : ").strip()

if not auth_token or not ct0:
    print("\nLoi: auth_token va ct0 khong duoc de trong!")
    sys.exit(1)

cookies = {
    "auth_token": auth_token,
    "ct0": ct0,
    "twid": twid,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=2)

print(f"\nDa luu cookies vao: {OUTPUT_FILE}")
print("Bay gio chay: python tweet_forward_bot.py")
