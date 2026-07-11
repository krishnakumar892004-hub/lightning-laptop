"""
Lightning Laptop -- Flask backend
Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify, g
from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lightning_laptop.db")

app = Flask(__name__)


# ---------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables (if missing) and seed sample laptops (only once)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            processor TEXT NOT NULL,
            ram TEXT NOT NULL,
            storage TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Placed',
            order_date TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
        )
   """)

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        sample_laptops = [
            ("Lightning Air 13", "Lightning", "Intel Core i5 13th Gen", "8GB", "512GB SSD", 54990, 12),
            ("Lightning Pro 15", "Lightning", "Intel Core i7 13th Gen", "16GB", "1TB SSD", 89990, 8),
            ("Lightning Gaming X", "Lightning", "AMD Ryzen 9 + RTX 4060", "16GB", "1TB SSD", 134990, 5),
            ("Lightning Book Slim", "Lightning", "Intel Core i3 12th Gen", "8GB", "256GB SSD", 39990, 20),
            ("Lightning Studio 16", "Lightning", "Apple M3 Pro", "18GB", "512GB SSD", 189990, 4),
            ("Lightning Voltage 14", "Lightning", "AMD Ryzen 7 7840U", "16GB", "512GB SSD", 74990, 10),
            ("Lightning Bolt Mini", "Lightning", "Intel Core i5 12th Gen", "8GB", "512GB SSD", 47990, 15),
            ("Lightning Ultra 17", "Lightning", "Intel Core i9 13th Gen + RTX 4070", "32GB", "2TB SSD", 219990, 2),
        ]
        cur.executemany(
            "INSERT INTO products (name, brand, processor, ram, storage, price, stock) VALUES (?,?,?,?,?,?,?)",
            sample_laptops,
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# Frontend route
# ---------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form["username"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])

    db = get_db()

    try:
        db.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password)
        )
        db.commit()
        return "Signup Successful!"
    except sqlite3.IntegrityError:
        return "Email already exists!"


# ---------------------------------------------------------------------
# Product API
# ---------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def get_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(dict(row))


@app.route("/api/products", methods=["POST"])
def add_product():
    """Admin: add a new laptop. Expects JSON body."""
    data = request.get_json(force=True)
    required = ["name", "brand", "processor", "ram", "storage", "price", "stock"]
    if not all(k in data for k in required):
        return jsonify({"error": f"Missing fields, need: {required}"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO products (name, brand, processor, ram, storage, price, stock) VALUES (?,?,?,?,?,?,?)",
        (data["name"], data["brand"], data["processor"], data["ram"],
         data["storage"], data["price"], data["stock"]),
    )
    db.commit()
    return jsonify({"success": True, "id": cur.lastrowid}), 201


# ---------------------------------------------------------------------
# Order API
# ---------------------------------------------------------------------
@app.route("/api/order", methods=["POST"])
def place_order():
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    items = data.get("items", [])

    if not name or not phone or not address or not items:
        return jsonify({"success": False, "error": "Missing name, phone, address or items"}), 400

    db = get_db()
    order_ids = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)

        product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if product is None:
            return jsonify({"success": False, "error": f"Product {product_id} not found"}), 404
        if product["stock"] < quantity:
            return jsonify({"success": False, "error": f"Not enough stock for {product['name']}"}), 400

        total_price = product["price"] * quantity

        cur = db.execute(
            """INSERT INTO orders
               (product_id, product_name, quantity, total_price, customer_name, phone, address, status, order_date)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (product_id, product["name"], quantity, total_price, name, phone, address, "Placed", now),
        )
        db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        order_ids.append(cur.lastrowid)

    db.commit()
    return jsonify({"success": True, "order_ids": order_ids})


@app.route("/api/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(dict(row))


@app.route("/api/orders", methods=["GET"])
def list_orders():
    """Admin: view all orders."""
    db = get_db()
    rows = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/order/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):
    """Admin: update order status e.g. Placed -> Shipped -> Delivered."""
    data = request.get_json(force=True)
    status = data.get("status")
    if status not in ("Placed", "Shipped", "Delivered", "Cancelled"):
        return jsonify({"error": "Invalid status"}), 400

    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    return jsonify({"success": True})


# ---------------------------------------------------------------------
# Small stats endpoint (used on homepage hero)
# ---------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def stats():
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    row = db.execute(
        "SELECT COUNT(*) as c FROM orders WHERE order_date LIKE ?", (today + "%",)
    ).fetchone()
    return jsonify({"orders_today": row["c"]})


import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
