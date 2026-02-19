import sqlite3
from pathlib import Path


def get_connection(db_path: str = "icecream_factory.db") -> sqlite3.Connection:
    path = Path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'kg',
            cost_per_unit REAL NOT NULL CHECK (cost_per_unit >= 0),
            sale_price_per_unit REAL NOT NULL CHECK (sale_price_per_unit >= 0)
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            contact_info TEXT
        );

        CREATE TABLE IF NOT EXISTS raw_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            unit TEXT NOT NULL,
            stock_qty REAL NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
            reorder_level REAL NOT NULL DEFAULT 0 CHECK (reorder_level >= 0)
        );

        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            qty_per_unit REAL NOT NULL CHECK (qty_per_unit > 0),
            UNIQUE(product_id, material_id),
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES raw_materials(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL UNIQUE,
            qty REAL NOT NULL DEFAULT 0 CHECK (qty >= 0),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS production_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            produced_qty REAL NOT NULL CHECK (produced_qty > 0),
            produced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            note TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            sold_qty REAL NOT NULL CHECK (sold_qty > 0),
            sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            channel TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            qty REAL NOT NULL CHECK (qty > 0),
            price REAL NOT NULL CHECK (price >= 0),
            ordered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (material_id) REFERENCES raw_materials(id)
        );
        """
    )
    conn.commit()
