import sqlite3

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    stock INTEGER,
    unit_cost REAL,
    selling_price REAL,
    reorder_level INTEGER,
    supplier TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    movement_type TEXT,
    quantity INTEGER,
    timestamp TEXT
    )
""")

conn.commit()
conn.close()

print("Tables created!")
