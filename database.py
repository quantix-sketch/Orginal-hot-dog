import sqlite3
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name_uz TEXT NOT NULL,
            name_ru TEXT NOT NULL,
            emoji   TEXT DEFAULT '🍽️',
            active  INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER REFERENCES categories(id),
            name_uz     TEXT NOT NULL,
            name_ru     TEXT NOT NULL,
            description_uz TEXT DEFAULT '',
            description_ru TEXT DEFAULT '',
            price       INTEGER NOT NULL,
            image_url   TEXT DEFAULT '',
            active      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY,
            username   TEXT,
            full_name  TEXT,
            phone      TEXT,
            lang       TEXT DEFAULT 'uz',
            lat        REAL,
            lng        REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER REFERENCES users(id),
            status       TEXT DEFAULT 'pending',
            total_price  INTEGER DEFAULT 0,
            address      TEXT DEFAULT '',
            delivery_type TEXT DEFAULT 'delivery',
            location_lat REAL,
            location_lng REAL,
            promo_code   TEXT DEFAULT '',
            discount_amount INTEGER DEFAULT 0,
            payment_type TEXT DEFAULT '',
            paid         INTEGER DEFAULT 0,
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            qty        INTEGER DEFAULT 1,
            price      INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS promo_codes (
            code       TEXT PRIMARY KEY,
            discount_type TEXT DEFAULT 'percent',
            discount_value INTEGER NOT NULL,
            min_total  INTEGER DEFAULT 0,
            active     INTEGER DEFAULT 1
        );
    """)

    ensure_column(c, "orders", "delivery_type", "TEXT DEFAULT 'delivery'")
    ensure_column(c, "orders", "location_lat", "REAL")
    ensure_column(c, "orders", "location_lng", "REAL")
    ensure_column(c, "orders", "promo_code", "TEXT DEFAULT ''")
    ensure_column(c, "orders", "discount_amount", "INTEGER DEFAULT 0")
    ensure_column(c, "users", "lat", "REAL")
    ensure_column(c, "users", "lng", "REAL")

    # Demo ma'lumotlar
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        cats = [
            ("Xot-doglar", "Хот-доги", "🌭"),
            ("Burgerlar",  "Бургеры",  "🍔"),
            ("Ichimliklar","Напитки",  "🥤"),
            ("Qo'shimchalar","Добавки", "🍟"),
        ]
        c.executemany("INSERT INTO categories (name_uz, name_ru, emoji) VALUES (?,?,?)", cats)

        prods = [
            (1, "Klassik Xot-dog",    "Классик Хот-дог",    "Yumshoq non, sosis, ketchup, mayonez", "Мягкая булочка, сосиска, кетчуп, майонез", 15000, ""),
            (1, "Cheese Xot-dog",     "Чиз Хот-дог",        "Klassik + qo'shimcha pishloq",         "Классик + дополнительный сыр",             18000, ""),
            (1, "XXL Xot-dog",        "XXL Хот-дог",        "Katta hajm, ikki sosis",               "Большой размер, две сосиски",               25000, ""),
            (2, "Orginal Burger",     "Оригинал Бургер",    "Mol go'shti, salat, tomat, sous",      "Говядина, салат, томат, соус",             22000, ""),
            (2, "Double Burger",      "Дабл Бургер",        "Ikki qatlam go'sht",                   "Двойная котлета",                          30000, ""),
            (3, "Coca-Cola 0.5L",     "Кока-Кола 0.5Л",    "Sovuq Coca-Cola",                      "Холодная Кока-Кола",                        8000, ""),
            (3, "Lipton 0.5L",        "Липтон 0.5Л",       "Muz choy",                             "Холодный чай",                              7000, ""),
            (4, "Kartoshka fri",      "Картошка фри",       "Tuz bilan",                            "С солью",                                  10000, ""),
            (4, "Sous (ketchup)",     "Соус (кетчуп)",     "Qo'shimcha sous",                      "Дополнительный соус",                       2000, ""),
        ]
        c.executemany("""INSERT INTO products
            (category_id,name_uz,name_ru,description_uz,description_ru,price,image_url)
            VALUES (?,?,?,?,?,?,?)""", prods)

    c.execute("SELECT COUNT(*) FROM promo_codes")
    if c.fetchone()[0] == 0:
        c.execute(
            """INSERT INTO promo_codes
            (code, discount_type, discount_value, min_total, active)
            VALUES (?, ?, ?, ?, ?)""",
            ("HOTDOG10", "percent", 10, 30000, 1)
        )

    conn.commit()
    conn.close()

# ── Helpers ──────────────────────────────────────────────

def ensure_column(cursor, table, column, definition):
    existing = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def get_or_create_user(uid, username, full_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?,?,?)",
              (uid, username, full_name))
    conn.commit()
    row = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row)

def set_user_lang(uid, lang):
    conn = get_conn()
    conn.execute("UPDATE users SET lang=? WHERE id=?", (lang, uid))
    conn.commit(); conn.close()

def set_user_phone(uid, phone):
    conn = get_conn()
    conn.execute("UPDATE users SET phone=? WHERE id=?", (phone, uid))
    conn.commit(); conn.close()

def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM categories WHERE active=1").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_products(category_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE category_id=? AND active=1", (category_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_active_products():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM products
        WHERE active=1
        ORDER BY category_id, id""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product(product_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def validate_order_items(items):
    if not isinstance(items, list):
        raise ValueError("Buyurtma mahsulotlari noto'g'ri formatda")

    normalized = []
    total = 0
    conn = get_conn()
    try:
        for item in items:
            try:
                product_id = int(item.get("id"))
                qty = int(item.get("qty", 0))
            except (TypeError, ValueError):
                raise ValueError("Mahsulot ID yoki soni noto'g'ri") from None

            if qty < 1 or qty > 50:
                raise ValueError("Mahsulot soni 1 dan 50 gacha bo'lishi kerak")

            product = conn.execute(
                "SELECT * FROM products WHERE id=? AND active=1",
                (product_id,)
            ).fetchone()
            if product is None:
                raise ValueError(f"Mahsulot topilmadi: {product_id}")

            product = dict(product)
            line_total = product["price"] * qty
            total += line_total
            normalized.append({
                "id": product["id"],
                "name_uz": product["name_uz"],
                "name_ru": product["name_ru"],
                "qty": qty,
                "price": product["price"],
            })
    finally:
        conn.close()

    if not normalized:
        raise ValueError("Savat bo'sh")
    return normalized, total

def get_active_promos():
    conn = get_conn()
    rows = conn.execute("""
        SELECT code, discount_type, discount_value, min_total
        FROM promo_codes
        WHERE active=1
        ORDER BY code""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def apply_promo(code, subtotal):
    code = (code or "").strip().upper()
    if not code:
        return "", 0

    conn = get_conn()
    promo = conn.execute(
        "SELECT * FROM promo_codes WHERE code=? AND active=1",
        (code,)
    ).fetchone()
    conn.close()

    if promo is None:
        raise ValueError("Promo kod topilmadi")
    promo = dict(promo)
    if subtotal < int(promo["min_total"] or 0):
        raise ValueError("Promo kod uchun minimal summa yetarli emas")

    if promo["discount_type"] == "amount":
        discount = int(promo["discount_value"])
    else:
        discount = subtotal * int(promo["discount_value"]) // 100
    discount = max(0, min(discount, subtotal))
    return code, discount

def create_order(
    user_id, items, total, address, payment_type,
    delivery_type="delivery", location_lat=None, location_lng=None,
    promo_code="", discount_amount=0
):
    items, total = validate_order_items(items)
    final_total = max(0, total - int(discount_amount or 0))
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO orders
        (user_id, total_price, address, payment_type, delivery_type,
         location_lat, location_lng, promo_code, discount_amount)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            user_id, final_total, address, payment_type, delivery_type,
            location_lat, location_lng, promo_code, int(discount_amount or 0)
        )
    )
    order_id = c.lastrowid
    for item in items:
        c.execute("INSERT INTO order_items (order_id, product_id, qty, price) VALUES (?,?,?,?)",
                  (order_id, item['id'], item['qty'], item['price']))
    conn.commit(); conn.close()
    return order_id

def get_order(order_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if row is None:
        conn.close()
        return None
    order = dict(row)
    items = conn.execute("""
        SELECT oi.*, p.name_uz, p.name_ru FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id=?""", (order_id,)).fetchall()
    order['items'] = [dict(i) for i in items]
    conn.close()
    return order

def mark_order_paid(order_id):
    conn = get_conn()
    conn.execute("UPDATE orders SET paid=1, status='confirmed' WHERE id=?", (order_id,))
    conn.commit(); conn.close()

def set_order_payment(order_id, payment_type, paid=False):
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET payment_type=?, paid=? WHERE id=?",
        (payment_type, 1 if paid else 0, order_id)
    )
    conn.commit(); conn.close()

def update_order_status(order_id, status):
    conn = get_conn()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit(); conn.close()

def get_all_orders(limit=50):
    conn = get_conn()
    rows = conn.execute("""
        SELECT o.*, u.full_name, u.phone FROM orders o
        LEFT JOIN users u ON u.id = o.user_id
        ORDER BY o.created_at DESC LIMIT ?""", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_products():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, c.name_uz as cat_name FROM products p
        LEFT JOIN categories c ON c.id = p.category_id
        ORDER BY p.category_id, p.id""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def category_exists(category_id):
    conn = get_conn()
    row = conn.execute("SELECT id FROM categories WHERE id=?", (category_id,)).fetchone()
    conn.close()
    return row is not None

def add_product(cat_id, name_uz, name_ru, desc_uz, desc_ru, price):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO products
        (category_id, name_uz, name_ru, description_uz, description_ru, price)
        VALUES (?,?,?,?,?,?)""", (cat_id, name_uz, name_ru, desc_uz, desc_ru, price))
    product_id = c.lastrowid
    conn.commit(); conn.close()
    return product_id

def toggle_product(product_id):
    conn = get_conn()
    row = conn.execute("SELECT active FROM products WHERE id=?", (product_id,)).fetchone()
    if row is None:
        conn.close()
        return None
    new_status = 0 if row["active"] else 1
    conn.execute("UPDATE products SET active=? WHERE id=?", (new_status, product_id))
    conn.commit(); conn.close()
    return new_status

def update_product_price(product_id, price):
    conn = get_conn()
    cur = conn.execute("UPDATE products SET price=? WHERE id=?", (price, product_id))
    conn.commit(); conn.close()
    return cur.rowcount > 0
