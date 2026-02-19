DROP TABLE IF EXISTS mes_events CASCADE;
DROP TABLE IF EXISTS erp_procurements CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS production_batches CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    shift TEXT NOT NULL,
    phone TEXT NOT NULL
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    unit TEXT NOT NULL,
    min_threshold NUMERIC NOT NULL
);

CREATE TABLE production_batches (
    id SERIAL PRIMARY KEY,
    flavor TEXT NOT NULL,
    volume_liters NUMERIC NOT NULL,
    status TEXT NOT NULL,
    operator_name TEXT NOT NULL,
    started_at TEXT NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    client_name TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity_boxes INTEGER NOT NULL,
    due_date DATE NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE erp_procurements (
    id SERIAL PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    material TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    unit TEXT NOT NULL,
    total_cost NUMERIC NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE mes_events (
    id SERIAL PRIMARY KEY,
    line_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    reason TEXT NOT NULL,
    quality_score NUMERIC NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
