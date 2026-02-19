DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS production_batches;
DROP TABLE IF EXISTS orders;

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    shift TEXT NOT NULL,
    phone TEXT NOT NULL
);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    min_threshold REAL NOT NULL
);

CREATE TABLE production_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flavor TEXT NOT NULL,
    volume_liters REAL NOT NULL,
    status TEXT NOT NULL,
    operator_name TEXT NOT NULL,
    started_at TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity_boxes INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL
);
