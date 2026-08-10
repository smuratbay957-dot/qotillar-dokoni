import asyncio
import os
import random
import secrets
import sqlite3
import string
import sys
import threading
import urllib.parse
import urllib.request
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "qotillar_dokoni.db")
SECRET_FILE = os.path.join(BASE_DIR, "secret.key")

load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

sys.path.insert(0, os.path.join(BASE_DIR, ".."))
import db as botdb

ADMIN_CODE = os.getenv("ADMIN_CODE", "MURTHEHELPa").strip().lower()
ADMIN_CODE2 = os.getenv("ADMIN_CODE2", "MURTHEHELPaalpa").strip().lower()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()
WEB_URL = os.getenv("WEB_URL", "").strip()
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

VIP_DISCOUNT = int(os.getenv("VIP_DISCOUNT", "20"))

COLORS = ["red", "purple", "yellow", "green"]

COLOR_META = {
    "red": {"label": "QIZIL KOD", "sub": "QOTIL", "hex": "#ff1e1e"},
    "purple": {"label": "BINAFSHA KOD", "sub": "JOSUS", "hex": "#b026ff"},
    "yellow": {"label": "SARIQ KOD", "sub": "TOZALOVCHI", "hex": "#ffd60a"},
    "green": {"label": "YASHIL KOD", "sub": "HIMOYALANGAN", "hex": "#2bff88"},
}

CATALOG = {
    "red": {
        "red_knife": {"name": "JANGOVAR PICHQOQ", "price": 250, "desc": "Zarbdor, ovozsiz va halokatli."},
        "red_gun": {"name": "TO'PPONCHA", "price": 600, "desc": "Kompakt, tez va aniq."},
        "red_poison": {"name": "YASHIRIN ZAHAR", "price": 400, "desc": "Iz qoldirmaydigan modda."},
        "red_bomb": {"name": "PORTLOVCHI PAKET", "price": 800, "desc": "Masofadan boshqariladi."},
        "red_vest": {"name": "KEVLAR JILET", "price": 500, "desc": "O'q o'tkazmaydigan himoya."},
    },
    "purple": {
        "purple_bug": {"name": "QULOQ SOLISH MOSLAMASI", "price": 300, "desc": "Hamma narsani eshitadi."},
        "purple_cam": {"name": "YASHIRIN KAMERA", "price": 350, "desc": "Ko'zga ko'rinmas nazorat."},
        "purple_gps": {"name": "GPS KUZATUVCHI", "price": 250, "desc": "Har bir qadamni kuzatadi."},
        "purple_radio": {"name": "SHIFRLANGAN ALOQA", "price": 450, "desc": "Tinglab bo'lmaydigan kanal."},
    },
    "yellow": {
        "yellow_kit": {"name": "TOZALASH TO'PLAMI", "price": 200, "desc": "Hech qanday iz qoldirmaydi."},
        "yellow_cleaner": {"name": "NEUTRALIZATOR", "price": 350, "desc": "Qiyin joylarni ham tozalaydi."},
        "yellow_det": {"name": "IZ DETEKTORI", "price": 400, "desc": "Qolgan izlarni topadi."},
        "yellow_docs": {"name": "SOXTA HUJJATLAR", "price": 500, "desc": "Yangi shaxs, yangi hayot."},
    },
    "green": {
        "green_safe": {"name": "HIMOYA KAPSULASI", "price": 600, "desc": "Hujumdan to'liq himoya."},
        "green_car": {"name": "QOCHISH AVTOMOBILI", "price": 900, "desc": "Eng xavfli vaziyatda ham uchib ketadi."},
        "green_med": {"name": "TIBBIY TO'PLAM", "price": 300, "desc": "Jarohatni joyida davolaydi."},
        "green_mask": {"name": "TANIB BO'LMAS NIQOB", "price": 250, "desc": "Sizni hech kim tanimaydi."},
    },
}


def is_vip(code):
    return bool(code) and code.lower().endswith("vipcode")


def effective_price(price, vip):
    if vip:
        return int(price * (100 - VIP_DISCOUNT) / 100)
    return price


def product_image(pid):
    return f"https://picsum.photos/seed/{pid}/600/400"


def tg_send(chat_id, text):
    if not BOT_TOKEN or not chat_id:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def load_secret():
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
            if key:
                return key
    key = secrets.token_hex(32)
    with open(SECRET_FILE, "w", encoding="utf-8") as f:
        f.write(key)
    return key


app = Flask(__name__)
app.secret_key = load_secret()
app.config["SESSION_COOKIE_NAME"] = "murthehelp_session"


_loop = None
_bot = None
_dp = None
_aiogram_ready = False
_aiogram_lock = threading.Lock()


def _ensure_aiogram():
    global _loop, _bot, _dp, _aiogram_ready
    if _aiogram_ready or not BOT_TOKEN:
        return
    with _aiogram_lock:
        if _aiogram_ready:
            return
        import handlers
        from aiohttp import ClientSession
        from aiohttp.hdrs import USER_AGENT
        from aiohttp.http import SERVER_SOFTWARE
        from aiogram import Bot, Dispatcher
        from aiogram.client.default import DefaultBotProperties
        from aiogram.client.session.aiohttp import AiohttpSession
        from aiogram.enums import ParseMode

        class EnvProxySession(AiohttpSession):
            async def create_session(self) -> ClientSession:
                if self._should_reset_connector:
                    await self.close()
                if self._session is None or self._session.closed:
                    from aiogram.__meta__ import __version__

                    self._session = ClientSession(
                        connector=self._connector_type(**self._connector_init),
                        headers={
                            USER_AGENT: f"{SERVER_SOFTWARE} aiogram/{__version__}",
                        },
                        trust_env=True,
                    )
                    self._should_reset_connector = False
                return self._session

        _loop = asyncio.new_event_loop()
        threading.Thread(target=_loop.run_forever, daemon=True).start()
        _bot = Bot(
            token=BOT_TOKEN,
            session=EnvProxySession(),
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )
        _dp = Dispatcher()
        _dp.include_router(handlers.router)
        _aiogram_ready = True
        print("AIOGRAM READY: loop thread started", flush=True)


def setup_webhook():
    if not BOT_TOKEN or not WEBHOOK_SECRET or not WEB_URL.startswith("https"):
        return
    url = f"{WEB_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET}"
    data = urllib.parse.urlencode({"url": url, "drop_pending_updates": "true"}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook", data=data
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            r.read()
    except Exception:
        pass


threading.Thread(target=setup_webhook, daemon=True).start()


def get_db():
    if "_db" not in g:
        g._db = sqlite3.connect(DB_PATH)
        g._db.row_factory = sqlite3.Row
    return g._db


@app.teardown_appcontext
def close_db(_exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db():
    botdb.init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                color TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )


def generate_code(length=16):
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def lookup_code(code):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT code, color, note FROM codes WHERE code = ?", (code,)
        ).fetchone()
    return row


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("gate"))
        return view(*args, **kwargs)

    return wrapper


def user_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "user":
            return redirect(url_for("gate"))
        return view(*args, **kwargs)

    return wrapper


@app.context_processor
def inject_globals():
    return {"color_meta": COLOR_META, "colors": COLORS}


@app.route("/")
def gate():
    return render_template("gate.html")


@app.route("/debug")
def debug():
    return {
        "env_file_exists": os.path.exists(os.path.join(BASE_DIR, "..", ".env")),
        "bot_token_set": bool(BOT_TOKEN),
        "admin_id": ADMIN_ID,
        "webhook_secret": WEBHOOK_SECRET,
        "web_url": WEB_URL,
        "aiogram_ready": _aiogram_ready,
        "db_path": DB_PATH,
        "webhook_endpoint": f"/webhook/{WEBHOOK_SECRET}",
    }


@app.route("/debug/net")
def debug_net():
    import urllib.request

    results = {}
    for name, url in [
        ("telegram", "https://api.telegram.org"),
        ("google", "https://www.google.com"),
    ]:
        try:
            r = urllib.request.urlopen(url, timeout=8)
            results[name] = f"OK {r.status}"
        except Exception as e:
            results[name] = f"FAIL {type(e).__name__}: {e}"
    results["https_proxy"] = os.environ.get("HTTPS_PROXY") or os.environ.get(
        "https_proxy"
    )
    results["http_proxy"] = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    results["no_proxy"] = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")
    return results


@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    if not WEBHOOK_SECRET or token != WEBHOOK_SECRET:
        return "forbidden", 403
    import traceback

    try:
        _ensure_aiogram()
        if not _dp or not _bot or not _loop:
            print("WEBHOOK: aiogram not ready", flush=True)
            return "ok", 200
        from aiogram.types import Update

        update = Update.model_validate(request.get_json(force=True))
        print(
            f"WEBHOOK HIT: update_id={update.update_id} chat={update.message.chat.id if update.message else '?'}",
            flush=True,
        )
        fut = asyncio.run_coroutine_threadsafe(
            _dp.feed_webhook_update(_bot, update), _loop
        )
        try:
            fut.result(timeout=30)
            print(f"FEED OK: update_id={update.update_id}", flush=True)
        except Exception:
            exc = traceback.format_exc()
            print(f"FEED FAILED: update_id={update.update_id}\n{exc}", flush=True)
    except Exception:
        exc = traceback.format_exc()
        print(f"WEBHOOK ROUTE ERROR:\n{exc}", flush=True)
    return "ok", 200


@app.route("/login", methods=["POST"])
def login():
    raw = request.form.get("code", "").strip()
    code = raw.lower()
    if not code:
        flash("[!] KOD KIRITING")
        return redirect(url_for("gate"))
    if code == ADMIN_CODE:
        session.clear()
        session["pending_admin"] = True
        flash("[+] BIRINCHI QADAM OK -- ENDI ADMIN PAROLINI KIRITING")
        return redirect(url_for("gate"))
    row = lookup_code(code)
    if row:
        session.clear()
        session["role"] = "user"
        session["code"] = row["code"]
        session["color"] = row["color"]
        session["vip"] = is_vip(row["code"])
        return redirect(url_for("shop"))
    flash("[!] NOTO'G'RI KOD -- KIRISH RAD ETILDI")
    return redirect(url_for("gate"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("gate"))


@app.route("/admin/verify", methods=["POST"])
def admin_verify():
    if not session.get("pending_admin"):
        flash("[!] AVVAL BIRINCHI QADAMNI BAJARING")
        return redirect(url_for("gate"))
    password2 = request.form.get("password2", "").strip().lower()
    if password2 != ADMIN_CODE2:
        session.pop("pending_admin", None)
        flash("[!] NOTO'G'RI PAROL -- KIRISH RAD ETILDI")
        return redirect(url_for("gate"))
    session.clear()
    session["role"] = "admin"
    flash("[+] XUSH KELIBSIZ, MURTHEHELP")
    return redirect(url_for("admin"))


@app.route("/admin")
@admin_required
def admin():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.id, c.code, c.color, c.note, c.created_at,
                   u.name AS uname, u.balance
            FROM codes c
            LEFT JOIN users u ON u.code = c.code
            ORDER BY c.id DESC
            """
        ).fetchall()
    orders = botdb.get_all_orders()
    return render_template("admin.html", codes=rows, orders=orders)


@app.route("/admin/create", methods=["POST"])
@admin_required
def create():
    color = request.form.get("color")
    code = request.form.get("code", "").strip().lower()
    note = request.form.get("note", "").strip()

    if color not in COLORS:
        flash("[!] NOTO'G'RI RANG TANLANDI")
        return redirect(url_for("admin"))
    if not code:
        code = generate_code()
    if code == ADMIN_CODE:
        flash("[!] BU KOD ZAXIRALANGAN (ADMIN KODI)")
        return redirect(url_for("admin"))
    if not code.isalnum() or len(code) < 4 or len(code) > 32:
        flash("[!] KOD 4-32 BELGI, FAQAT HARFLAR VA RAQAMLAR BO'LISHI KERAK")
        return redirect(url_for("admin"))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO codes (code, color, note) VALUES (?, ?, ?)",
                (code, color, note),
            )
    except sqlite3.IntegrityError:
        flash("[!] BUNDAY KOD AVVAL YARATILGAN")
        return redirect(url_for("admin"))
    flash(f"[+] {COLOR_META[color]['label']} YARATILDI: {code}")
    return redirect(url_for("admin"))


@app.route("/admin/revoke/<int:cid>", methods=["POST"])
@admin_required
def revoke(cid):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM codes WHERE id = ?", (cid,))
    flash("[-] KOD O'CHIRILDI")
    return redirect(url_for("admin"))


@app.route("/admin/order/reply/<int:oid>", methods=["POST"])
@admin_required
def order_reply(oid):
    order = botdb.get_order(oid)
    if not order:
        flash("[!] BUYURTMA TOPILMADI")
        return redirect(url_for("admin"))
    answer = request.form.get("answer", "").strip()
    try:
        final_price = int(request.form.get("final_price", "0").strip())
    except ValueError:
        final_price = 0
    if final_price < 1:
        flash("[!] NARX 1 DAN KAM BO'LMAYDI")
        return redirect(url_for("admin"))
    botdb.reply_order(oid, answer, final_price)
    flash(f"[+] BUYURTMA #{oid}GA JAVOB YUBORILDI: {final_price} KREDIT")
    if order["user_id"]:
        buyer = botdb.get_user(order["user_id"])
        msg = (
            f"[MURTHEHELP] Buyurtma #{oid}\n"
            f"Mahsulot: {order['name']}\n"
            f"Admin javobi: {answer or '-'}\n"
            f"Yakuniy narx: {final_price} KREDIT\n"
            f"Saytdagi /buyurtmalar sahifasidan tasdiqlang."
        )
        tg_send(order["user_id"], msg)
    return redirect(url_for("admin"))


@app.route("/shop")
@user_required
def shop():
    color = session.get("color", "green")
    code = session.get("code", "")
    vip = session.get("vip", False)
    linked = botdb.get_user_by_code(code)
    balance = botdb.get_user(linked["user_id"])["balance"] if linked else None
    products = [
        (
            pid,
            {
                **item,
                "price": effective_price(item["price"], vip),
                "orig": item["price"],
                "img": product_image(pid),
            },
        )
        for pid, item in CATALOG.get(color, {}).items()
    ]
    return render_template(
        "shop.html",
        code=code,
        meta=COLOR_META[color],
        products=products,
        balance=balance,
        vip=vip,
        vip_discount=VIP_DISCOUNT,
    )


@app.route("/order", methods=["POST"])
@user_required
def order():
    pid = request.form.get("pid", "")
    msg = request.form.get("message", "").strip()
    color = session.get("color", "")
    vip = session.get("vip", False)
    item = CATALOG.get(color, {}).get(pid)
    if not item:
        flash("[!] MAHSULOT TOPILMADI")
        return redirect(url_for("shop"))
    if not msg:
        msg = "Bu mahsulotni olmoqchiman. Narxi qancha?"
    linked = botdb.get_user_by_code(session.get("code"))
    user_id = linked["user_id"] if linked else None
    price = effective_price(item["price"], vip)
    oid = botdb.create_order(
        session.get("code"),
        color,
        user_id,
        pid,
        item["name"],
        msg,
        price,
        vip,
    )
    tg_send(
        ADMIN_ID,
        "[MURTHEHELP] YANGI BUYURTMA #{}\n"
        "Mahsulot: {}\n"
        "Kod: {}\n"
        "{}\n"
        "Xabar: {}\n"
        "Tasdiq: sayt admin panelida".format(oid, item["name"], session.get("code"), "VIP" if vip else "ODDIY", msg),
    )
    flash(f"[+] Buyurtma #{oid} yuborildi. Admin javobini kuting. Javob bot'ga ham keladi!")
    return redirect(url_for("orders"))


@app.route("/orders")
@user_required
def orders():
    rows = botdb.get_orders_by_code(session.get("code"))
    return render_template("orders.html", orders=rows)


@app.route("/orders/confirm/<int:oid>", methods=["POST"])
@user_required
def order_confirm(oid):
    order = botdb.get_order(oid)
    if not order or order["code"] != session.get("code"):
        flash("[!] BUYURTMA TOPILMADI")
        return redirect(url_for("orders"))
    if order["status"] != "answered":
        flash("[!] BUYURTMA HALI TASDIQLANADIGAN HOLATDA EMAS")
        return redirect(url_for("orders"))
    linked = botdb.get_user_by_code(session.get("code"))
    if not linked:
        flash("[!] XARIDNI TASDIQLASH UCHUN AVVAL BOT'DA /kirish <kod> QILING.")
        return redirect(url_for("orders"))
    user = botdb.get_user(linked["user_id"])
    price = order["final_price"] or order["base_price"]
    if user["balance"] < price:
        flash(f"[!] KREDITINGIZ YETARLI EMAS. BALANS: {user['balance']}")
        return redirect(url_for("orders"))
    botdb.spend(user["user_id"], price)
    botdb.add_item(user["user_id"], order["pid"])
    botdb.confirm_order(oid)
    flash(f"[+] SOTIB OLINDI: {order['name']} -- {price} KREDIT. TELEGRAM OMBORINGIZGA TUSHDI!")
    tg_send(
        ADMIN_ID,
        f"[MURTHEHELP] Buyurtma #{oid} tasdiqlandi!\n"
        f"Mahsulot: {order['name']}\n"
        f"Yakuniy narx: {price} KREDIT\n"
        f"Xaridor kodi: {order['code']}",
    )
    return redirect(url_for("orders"))


@app.route("/vitrin")
@user_required
def vitrin():
    listings = botdb.get_active_listings()
    sold = botdb.get_recent_sold_listings(10)
    return render_template("vitrin.html", listings=listings, sold=sold)


@app.route("/vitrin/buy/<int:lid>", methods=["POST"])
@user_required
def vitrin_buy(lid):
    listing = botdb.get_listing(lid)
    if not listing or listing["status"] != "active":
        flash("[!] BU MAHSULOT ALLAQACHON SOTILGAN")
        return redirect(url_for("vitrin"))
    linked = botdb.get_user_by_code(session.get("code"))
    if not linked:
        flash("[!] XARID QILISH UCHUN AVVAL BOT'DA /kirish <kod> QILING.")
        return redirect(url_for("vitrin"))
    user = botdb.get_user(linked["user_id"])
    if user["balance"] < listing["price"]:
        flash(f"[!] KREDITINGIZ YETARLI EMAS. BALANS: {user['balance']}")
        return redirect(url_for("vitrin"))
    botdb.spend(user["user_id"], listing["price"])
    botdb.add_item(user["user_id"], f"listing:{lid}")
    botdb.credit(listing["seller_id"], listing["price"])
    state = botdb.decrement_stock(lid)
    sold_out = bool(state and state["stock"] <= 0)
    if sold_out:
        botdb.close_listing(lid, user["user_id"])
    tg_send(
        ADMIN_ID,
        f"[MURTHEHELP] Vitrindan xarid!\n"
        f"Mahsulot: {listing['name']}\n"
        f"Narx: {listing['price']} KREDIT\n"
        f"Qoldiq: {state['stock'] if state else 0} dona\n"
        f"Xaridor kodi: {session.get('code')}"
        + ("\n\n⚠️ BU MAHSULOT SOTILIB KETDI!" if sold_out else ""),
    )
    flash(
        f"[+] SOTIB OLINDI: {listing['name']} -- {listing['price']} KREDIT. "
        f"TELEGRAM OMBORINGIZGA TUSHDI!"
    )
    return redirect(url_for("vitrin"))


if __name__ == "__main__":
    init_db()
    print(f"* MURTHEHELP ishga tushdi: http://127.0.0.1:{PORT}")
    try:
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"* LAN orqali kirish: http://{ip}:{PORT}")
    except Exception:
        pass
    app.run(host=HOST, port=PORT, debug=False)
