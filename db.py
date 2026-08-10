import os
import sqlite3

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qotillar_dokoni.db")


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                code TEXT,
                balance INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                product_id TEXT,
                qty INTEGER,
                PRIMARY KEY (user_id, product_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                name TEXT,
                price INTEGER,
                photo_file_id TEXT,
                photo_url TEXT DEFAULT '',
                stock INTEGER DEFAULT 1,
                tier INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                buyer_id INTEGER
            )
            """
        )
        try:
            conn.execute("ALTER TABLE listings ADD COLUMN photo_url TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE listings ADD COLUMN stock INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE listings ADD COLUMN tier INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                color TEXT NOT NULL,
                note TEXT DEFAULT '',
                used_by INTEGER DEFAULT NULL,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        try:
            conn.execute("ALTER TABLE codes ADD COLUMN used_by INTEGER DEFAULT NULL")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                color TEXT,
                user_id INTEGER,
                pid TEXT,
                name TEXT,
                message TEXT DEFAULT '',
                base_price INTEGER,
                vip INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                answer TEXT DEFAULT '',
                final_price INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )


def ensure_user(user_id, name, start_balance):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO users (user_id, name, code, balance)
            VALUES (?, ?, NULL, ?)
            """,
            (user_id, name, start_balance),
        )


def get_user(user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id, name, code, balance FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def set_code(user_id, code):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET code = ? WHERE user_id = ?",
            (code, user_id),
        )


def spend(user_id, amount):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (amount, user_id),
        )


def credit(user_id, amount):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id),
        )


def add_item(user_id, product_id, qty=1):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO inventory (user_id, product_id, qty)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + ?
            """,
            (user_id, product_id, qty, qty),
        )


def get_inventory(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT product_id, qty FROM inventory WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return [(row["product_id"], row["qty"]) for row in rows]


def create_listing(seller_id, name, price, photo_file_id, photo_url="", stock=1, tier=1):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO listings (seller_id, name, price, photo_file_id, photo_url, stock, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (seller_id, name, price, photo_file_id, photo_url, stock, tier),
        )
        return cur.lastrowid


def get_active_listings():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, seller_id, name, price, photo_file_id, photo_url, stock, tier FROM listings WHERE status = 'active' ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def get_active_listings_by_tier(tier):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, seller_id, name, price, photo_file_id, photo_url, stock, tier FROM listings WHERE status = 'active' AND tier = ? ORDER BY id",
            (tier,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_listing(listing_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, seller_id, name, price, photo_file_id, photo_url, stock, tier, status FROM listings WHERE id = ?",
            (listing_id,),
        ).fetchone()
    return dict(row) if row else None


def decrement_stock(listing_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE listings SET stock = stock - 1 WHERE id = ? AND status = 'active'",
            (listing_id,),
        )
        row = conn.execute(
            "SELECT id, seller_id, name, price, stock FROM listings WHERE id = ?",
            (listing_id,),
        ).fetchone()
    return dict(row) if row else None


def unsell_listing(name, price):
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM listings WHERE status = 'active' AND name = ? AND price = ?",
            (name, price),
        )
        return cur.rowcount


def get_recent_sold_listings(limit=10):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, seller_id, name, price, photo_file_id, photo_url, stock FROM listings WHERE status != 'active' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def close_listing(listing_id, buyer_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE listings SET status = 'sold', buyer_id = ? WHERE id = ?",
            (buyer_id, listing_id),
        )


def get_code(code):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT code, color, note FROM codes WHERE code = ?",
            (code,),
        ).fetchone()
    return dict(row) if row else None


def use_code(code, user_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT code, color, note, used_by FROM codes WHERE code = ?",
            (code,),
        ).fetchone()
        if not row:
            return None
        if row["used_by"] is not None and row["used_by"] != user_id:
            return False
        conn.execute(
            "UPDATE codes SET used_by = ? WHERE code = ?",
            (user_id, code),
        )
    return {"code": row["code"], "color": row["color"], "note": row["note"]}


def get_user_by_code(code):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT u.user_id, u.name, u.code, u.balance
            FROM codes c
            JOIN users u ON u.user_id = c.used_by
            WHERE c.code = ?
            """,
            (code,),
        ).fetchone()
    return dict(row) if row else None


def stats():
    with get_conn() as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        codes = conn.execute("SELECT COUNT(*) FROM codes").fetchone()[0]
        listings = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE status = 'active'"
        ).fetchone()[0]
    return users, codes, listings


def create_order(code, color, user_id, pid, name, message, price, vip):
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO orders (code, color, user_id, pid, name, message, base_price, vip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (code, color, user_id, pid, name, message, price, 1 if vip else 0),
        )
        return cur.lastrowid


def get_order(order_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
    return dict(row) if row else None


def get_orders_by_code(code):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders WHERE code = ? ORDER BY id DESC",
            (code,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_orders():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def reply_order(order_id, answer, final_price):
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET status = 'answered', answer = ?, final_price = ? WHERE id = ?",
            (answer, final_price, order_id),
        )


def confirm_order(order_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE orders SET status = 'sold' WHERE id = ?",
            (order_id,),
        )


def complete_listing_order(order, price):
    try:
        lid = int(order["pid"].split(":", 1)[1])
    except (ValueError, IndexError):
        return False, "noto'g'ri buyurtma"
    listing = get_listing(lid)
    if not listing or listing["status"] != "active":
        return False, "mahsulot sotilib bo'lgan"
    user = get_user(order["user_id"])
    if not user:
        return False, "xaridor topilmadi"
    if user["balance"] < price:
        return False, "xaridorda kredit yetarli emas"
    spend(order["user_id"], price)
    add_item(order["user_id"], f"listing:{lid}")
    credit(listing["seller_id"], price)
    state = decrement_stock(lid)
    if state and state["stock"] <= 0:
        close_listing(lid, order["user_id"])
    confirm_order(order["id"])
    return True, listing["name"]
