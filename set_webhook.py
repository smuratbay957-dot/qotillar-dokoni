import urllib.parse
import urllib.request

from config import BOT_TOKEN, WEBHOOK_SECRET, WEB_URL


def main():
    if not BOT_TOKEN:
        raise SystemExit("[!] BOT_TOKEN .env da yo'q!")
    if not WEBHOOK_SECRET:
        raise SystemExit("[!] WEBHOOK_SECRET .env da yo'q!")
    if not WEB_URL.startswith("https"):
        raise SystemExit("[!] WEB_URL https bilan boshlanishi kerak (.env ni yangilang)!")
    url = f"{WEB_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}"
    data = urllib.parse.urlencode({"url": url, "drop_pending_updates": "true"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", data=data
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = r.read().decode()
    print(resp)
    if '"ok":true' in resp:
        print(f"[+] Webhook o'rnatildi: {url}")
    else:
        print("[!] Xatolik yuz berdi (yuqoriga qarang)")


if __name__ == "__main__":
    main()
