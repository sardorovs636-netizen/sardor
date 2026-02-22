-- IceFactory PostgreSQL schema
-- Информационная система автоматизации деятельности мороженого завода

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ===== Enums =====
CREATE TYPE user_role AS ENUM ('ADMIN', 'WAREHOUSE', 'TECHNOLOGIST', 'QC', 'SALES');
CREATE TYPE movement_type AS ENUM ('IN', 'OUT', 'ADJUSTMENT');
CREATE TYPE batch_status AS ENUM (
  'PLANNED',
  'IN_PROGRESS',
  'READY_FOR_QC',
  'APPROVED',
  'REJECTED',
  'BLOCKED',
  'COMPLETED'
);
CREATE TYPE qc_result AS ENUM ('PASS', 'FAIL');
CREATE TYPE order_status AS ENUM ('NEW', 'CONFIRMED', 'SHIPPED', 'CANCELLED');

-- ===== Reference tables =====
CREATE TABLE users (
  id                BIGSERIAL PRIMARY KEY,
  username          VARCHAR(100) NOT NULL UNIQUE,
  password_hash     TEXT NOT NULL,
  full_name         VARCHAR(255) NOT NULL,
  role              user_role NOT NULL,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE units (
  id                BIGSERIAL PRIMARY KEY,
  code              VARCHAR(20) NOT NULL UNIQUE,
  name              VARCHAR(100) NOT NULL UNIQUE,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE raw_materials (
  id                BIGSERIAL PRIMARY KEY,
  name              VARCHAR(255) NOT NULL UNIQUE,
  unit_id           BIGINT NOT NULL REFERENCES units(id),
  min_stock         NUMERIC(14,3) NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE suppliers (
  id                BIGSERIAL PRIMARY KEY,
  name              VARCHAR(255) NOT NULL UNIQUE,
  phone             VARCHAR(50),
  email             VARCHAR(255),
  address           TEXT,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
  id                BIGSERIAL PRIMARY KEY,
  name              VARCHAR(255) NOT NULL UNIQUE,
  unit_id           BIGINT NOT NULL REFERENCES units(id),
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE customers (
  id                BIGSERIAL PRIMARY KEY,
  name              VARCHAR(255) NOT NULL UNIQUE,
  phone             VARCHAR(50),
  email             VARCHAR(255),
  address           TEXT,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Raw material warehouse =====
CREATE TABLE raw_material_movements (
  id                BIGSERIAL PRIMARY KEY,
  material_id       BIGINT NOT NULL REFERENCES raw_materials(id),
  movement_type     movement_type NOT NULL,
  quantity          NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
  movement_date     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  supplier_id       BIGINT REFERENCES suppliers(id),
  batch_id          BIGINT,
  reason            TEXT,
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Recipes (BOM) =====
CREATE TABLE recipes (
  id                BIGSERIAL PRIMARY KEY,
  product_id        BIGINT NOT NULL REFERENCES products(id),
  version_number    INTEGER NOT NULL CHECK (version_number > 0),
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  valid_from        DATE NOT NULL DEFAULT CURRENT_DATE,
  valid_to          DATE,
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (product_id, version_number)
);

CREATE UNIQUE INDEX ux_recipes_active_per_product
  ON recipes(product_id)
  WHERE is_active = TRUE;

CREATE TABLE recipe_items (
  id                BIGSERIAL PRIMARY KEY,
  recipe_id         BIGINT NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  material_id       BIGINT NOT NULL REFERENCES raw_materials(id),
  consumption_norm  NUMERIC(14,4) NOT NULL CHECK (consumption_norm > 0),
  UNIQUE (recipe_id, material_id)
);

-- ===== Production batches =====
CREATE TABLE production_batches (
  id                BIGSERIAL PRIMARY KEY,
  batch_no          VARCHAR(50) NOT NULL UNIQUE,
  product_id        BIGINT NOT NULL REFERENCES products(id),
  recipe_id         BIGINT NOT NULL REFERENCES recipes(id),
  planned_quantity  NUMERIC(14,3) NOT NULL CHECK (planned_quantity > 0),
  produced_quantity NUMERIC(14,3) CHECK (produced_quantity >= 0),
  status            batch_status NOT NULL DEFAULT 'PLANNED',
  production_date   DATE NOT NULL DEFAULT CURRENT_DATE,
  responsible_id    BIGINT NOT NULL REFERENCES users(id),
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE raw_material_movements
  ADD CONSTRAINT fk_raw_movement_batch
  FOREIGN KEY (batch_id) REFERENCES production_batches(id);

CREATE TABLE batch_material_consumption (
  id                BIGSERIAL PRIMARY KEY,
  batch_id          BIGINT NOT NULL REFERENCES production_batches(id) ON DELETE CASCADE,
  material_id       BIGINT NOT NULL REFERENCES raw_materials(id),
  planned_quantity  NUMERIC(14,3) NOT NULL CHECK (planned_quantity > 0),
  actual_quantity   NUMERIC(14,3) CHECK (actual_quantity >= 0),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (batch_id, material_id)
);

CREATE TABLE batch_status_history (
  id                BIGSERIAL PRIMARY KEY,
  batch_id          BIGINT NOT NULL REFERENCES production_batches(id) ON DELETE CASCADE,
  old_status        batch_status,
  new_status        batch_status NOT NULL,
  changed_by        BIGINT NOT NULL REFERENCES users(id),
  changed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  comment           TEXT
);

-- ===== QC =====
CREATE TABLE qc_checks (
  id                BIGSERIAL PRIMARY KEY,
  batch_id          BIGINT NOT NULL UNIQUE REFERENCES production_batches(id) ON DELETE CASCADE,
  temperature_c     NUMERIC(6,2),
  fat_percent       NUMERIC(6,2),
  acidity_ph        NUMERIC(6,2),
  comment           TEXT,
  result            qc_result NOT NULL,
  checked_by        BIGINT NOT NULL REFERENCES users(id),
  checked_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Finished goods warehouse =====
CREATE TABLE finished_goods_movements (
  id                BIGSERIAL PRIMARY KEY,
  product_id        BIGINT NOT NULL REFERENCES products(id),
  movement_type     movement_type NOT NULL,
  quantity          NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
  movement_date     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  batch_id          BIGINT REFERENCES production_batches(id),
  order_id          BIGINT,
  reason            TEXT,
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===== Orders / shipping =====
CREATE TABLE customer_orders (
  id                BIGSERIAL PRIMARY KEY,
  order_no          VARCHAR(50) NOT NULL UNIQUE,
  customer_id       BIGINT NOT NULL REFERENCES customers(id),
  order_date        DATE NOT NULL DEFAULT CURRENT_DATE,
  status            order_status NOT NULL DEFAULT 'NEW',
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE customer_order_items (
  id                BIGSERIAL PRIMARY KEY,
  order_id          BIGINT NOT NULL REFERENCES customer_orders(id) ON DELETE CASCADE,
  product_id        BIGINT NOT NULL REFERENCES products(id),
  quantity          NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
  UNIQUE (order_id, product_id)
);

CREATE TABLE shipments (
  id                BIGSERIAL PRIMARY KEY,
  shipment_no       VARCHAR(50) NOT NULL UNIQUE,
  order_id          BIGINT NOT NULL REFERENCES customer_orders(id),
  shipment_date     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by        BIGINT NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE shipment_items (
  id                BIGSERIAL PRIMARY KEY,
  shipment_id       BIGINT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  product_id        BIGINT NOT NULL REFERENCES products(id),
  quantity          NUMERIC(14,3) NOT NULL CHECK (quantity > 0),
  batch_id          BIGINT REFERENCES production_batches(id),
  UNIQUE (shipment_id, product_id, batch_id)
);

ALTER TABLE finished_goods_movements
  ADD CONSTRAINT fk_fg_order
  FOREIGN KEY (order_id) REFERENCES customer_orders(id);

-- ===== Utility trigger for updated_at =====
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_units_updated_at
BEFORE UPDATE ON units
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_raw_materials_updated_at
BEFORE UPDATE ON raw_materials
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_suppliers_updated_at
BEFORE UPDATE ON suppliers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_production_batches_updated_at
BEFORE UPDATE ON production_batches
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_customer_orders_updated_at
BEFORE UPDATE ON customer_orders
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ===== Views for stock balances =====
CREATE VIEW v_raw_material_stock AS
SELECT
  rm.id AS material_id,
  rm.name,
  rm.min_stock,
  COALESCE(SUM(CASE WHEN m.movement_type = 'IN' THEN m.quantity
                    WHEN m.movement_type = 'OUT' THEN -m.quantity
                    ELSE 0 END), 0) AS balance
FROM raw_materials rm
LEFT JOIN raw_material_movements m ON m.material_id = rm.id
GROUP BY rm.id, rm.name, rm.min_stock;

CREATE VIEW v_finished_goods_stock AS
SELECT
  p.id AS product_id,
  p.name,
  COALESCE(SUM(CASE WHEN m.movement_type = 'IN' THEN m.quantity
                    WHEN m.movement_type = 'OUT' THEN -m.quantity
                    ELSE 0 END), 0) AS balance
FROM products p
LEFT JOIN finished_goods_movements m ON m.product_id = p.id
GROUP BY p.id, p.name;

-- ===== Business checks as helper functions =====
CREATE OR REPLACE FUNCTION raw_material_balance(p_material_id BIGINT)
RETURNS NUMERIC AS $$
  SELECT COALESCE(SUM(CASE WHEN movement_type = 'IN' THEN quantity
                           WHEN movement_type = 'OUT' THEN -quantity
                           ELSE 0 END), 0)
  FROM raw_material_movements
  WHERE material_id = p_material_id;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION finished_goods_balance(p_product_id BIGINT)
RETURNS NUMERIC AS $$
  SELECT COALESCE(SUM(CASE WHEN movement_type = 'IN' THEN quantity
                           WHEN movement_type = 'OUT' THEN -quantity
                           ELSE 0 END), 0)
  FROM finished_goods_movements
  WHERE product_id = p_product_id;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION prevent_negative_raw_stock()
RETURNS TRIGGER AS $$
DECLARE
  current_balance NUMERIC;
BEGIN
  IF NEW.movement_type = 'OUT' THEN
    SELECT raw_material_balance(NEW.material_id) INTO current_balance;
    IF current_balance < NEW.quantity THEN
      RAISE EXCEPTION 'Недостаточно сырья. Остаток: %, попытка списания: %', current_balance, NEW.quantity;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION prevent_negative_finished_stock()
RETURNS TRIGGER AS $$
DECLARE
  current_balance NUMERIC;
BEGIN
  IF NEW.movement_type = 'OUT' THEN
    SELECT finished_goods_balance(NEW.product_id) INTO current_balance;
    IF current_balance < NEW.quantity THEN
      RAISE EXCEPTION 'Недостаточно готовой продукции. Остаток: %, попытка списания: %', current_balance, NEW.quantity;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_negative_raw_stock
BEFORE INSERT ON raw_material_movements
FOR EACH ROW EXECUTE FUNCTION prevent_negative_raw_stock();

CREATE TRIGGER trg_prevent_negative_finished_stock
BEFORE INSERT ON finished_goods_movements
FOR EACH ROW EXECUTE FUNCTION prevent_negative_finished_stock();

CREATE OR REPLACE FUNCTION apply_qc_result_to_batch()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.result = 'FAIL' THEN
    UPDATE production_batches SET status = 'BLOCKED' WHERE id = NEW.batch_id;
  ELSE
    UPDATE production_batches SET status = 'APPROVED' WHERE id = NEW.batch_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_apply_qc_result
AFTER INSERT OR UPDATE ON qc_checks
FOR EACH ROW EXECUTE FUNCTION apply_qc_result_to_batch();
