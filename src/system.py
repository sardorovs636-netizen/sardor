from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Iterable

from .db import get_connection, init_db


@dataclass
class FactorySystem:
    db_path: str = "icecream_factory.db"

    def _conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def bootstrap(self) -> None:
        with self._conn() as conn:
            init_db(conn)

    def add_product(self, name: str, category: str, cost: float, price: float, unit: str = "kg") -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO products(name, category, unit, cost_per_unit, sale_price_per_unit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, category, unit, cost, price),
            )
            product_id = cur.lastrowid
            conn.execute("INSERT INTO inventory(product_id, qty) VALUES (?, 0)", (product_id,))
            conn.commit()
            return int(product_id)

    def add_raw_material(self, name: str, unit: str, stock_qty: float, reorder_level: float) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO raw_materials(name, unit, stock_qty, reorder_level)
                VALUES (?, ?, ?, ?)
                """,
                (name, unit, stock_qty, reorder_level),
            )
            conn.commit()
            return int(cur.lastrowid)

    def set_recipe(self, product_id: int, materials: Iterable[tuple[int, float]]) -> None:
        with self._conn() as conn:
            for material_id, qty in materials:
                conn.execute(
                    """
                    INSERT INTO recipes(product_id, material_id, qty_per_unit)
                    VALUES (?, ?, ?)
                    ON CONFLICT(product_id, material_id)
                    DO UPDATE SET qty_per_unit=excluded.qty_per_unit
                    """,
                    (product_id, material_id, qty),
                )
            conn.commit()

    def produce(self, product_id: int, qty: float, note: str = "") -> None:
        with self._conn() as conn:
            recipe_rows = conn.execute(
                """
                SELECT material_id, qty_per_unit
                FROM recipes
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchall()

            if not recipe_rows:
                raise ValueError("Recipe is not configured for this product.")

            for row in recipe_rows:
                required = row["qty_per_unit"] * qty
                stock_row = conn.execute(
                    "SELECT stock_qty FROM raw_materials WHERE id = ?", (row["material_id"],)
                ).fetchone()
                if stock_row is None or stock_row["stock_qty"] < required:
                    raise ValueError("Not enough raw materials for production batch.")

            for row in recipe_rows:
                required = row["qty_per_unit"] * qty
                conn.execute(
                    "UPDATE raw_materials SET stock_qty = stock_qty - ? WHERE id = ?",
                    (required, row["material_id"]),
                )

            conn.execute(
                "INSERT INTO production_batches(product_id, produced_qty, note) VALUES (?, ?, ?)",
                (product_id, qty, note),
            )
            conn.execute(
                "UPDATE inventory SET qty = qty + ?, updated_at=CURRENT_TIMESTAMP WHERE product_id = ?",
                (qty, product_id),
            )
            conn.commit()

    def sell(self, product_id: int, qty: float, channel: str) -> None:
        with self._conn() as conn:
            stock = conn.execute("SELECT qty FROM inventory WHERE product_id = ?", (product_id,)).fetchone()
            if stock is None or stock["qty"] < qty:
                raise ValueError("Not enough finished products in inventory.")

            conn.execute(
                "INSERT INTO sales(product_id, sold_qty, channel) VALUES (?, ?, ?)",
                (product_id, qty, channel),
            )
            conn.execute(
                "UPDATE inventory SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP WHERE product_id = ?",
                (qty, product_id),
            )
            conn.commit()

    def inventory_report(self) -> list[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute(
                """
                SELECT p.name AS product, p.category, i.qty, p.unit, i.updated_at
                FROM inventory i
                JOIN products p ON p.id = i.product_id
                ORDER BY p.name
                """
            ).fetchall()

    def sales_analytics(self) -> list[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute(
                """
                SELECT
                    p.name AS product,
                    SUM(s.sold_qty) AS total_sold,
                    ROUND(SUM(s.sold_qty * p.sale_price_per_unit), 2) AS revenue,
                    ROUND(SUM(s.sold_qty * p.cost_per_unit), 2) AS estimated_cost,
                    ROUND(SUM(s.sold_qty * (p.sale_price_per_unit - p.cost_per_unit)), 2) AS gross_profit
                FROM sales s
                JOIN products p ON p.id = s.product_id
                GROUP BY p.name
                ORDER BY revenue DESC
                """
            ).fetchall()

    def low_materials_report(self) -> list[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute(
                """
                SELECT name, stock_qty, reorder_level, unit
                FROM raw_materials
                WHERE stock_qty <= reorder_level
                ORDER BY stock_qty ASC
                """
            ).fetchall()
