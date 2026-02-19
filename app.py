from __future__ import annotations

import html
import sqlite3
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "factory.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
STATIC_CSS_PATH = BASE_DIR / "static" / "styles.css"


def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def seed_data() -> None:
    with db_conn() as conn:
        c = conn.cursor()
        if c.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO employees(name, role, shift, phone) VALUES (?, ?, ?, ?)",
                [
                    ("Алиев Тимур", "Технолог", "Утро", "+998 90 101 11 22"),
                    ("Каримова Лола", "Оператор линии", "День", "+998 90 202 33 44"),
                    ("Умаров Бекзод", "Контролер качества", "Ночь", "+998 90 303 55 66"),
                ],
            )
        if c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO inventory(item_name, category, quantity, unit, min_threshold) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Молоко 3.2%", "Сырье", 750, "л", 200),
                    ("Сахар", "Сырье", 320, "кг", 100),
                    ("Клубничный топпинг", "Добавки", 95, "кг", 30),
                    ("Вафельный стаканчик", "Упаковка", 12000, "шт", 5000),
                ],
            )
        if c.execute("SELECT COUNT(*) FROM production_batches").fetchone()[0] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.executemany(
                "INSERT INTO production_batches(flavor, volume_liters, status, operator_name, started_at) VALUES (?, ?, ?, ?, ?)",
                [("Ваниль", 420, "В процессе", "Каримова Лола", now), ("Шоколад", 500, "Завершено", "Алиев Тимур", now)],
            )
        if c.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO orders(client_name, product, quantity_boxes, due_date, status) VALUES (?, ?, ?, ?, ?)",
                [("SuperMart", "Пломбир ванильный", 120, "2026-03-01", "Новый"), ("Sweet House", "Эскимо шоколадное", 80, "2026-03-03", "В сборке")],
            )




def notice_text(code: str) -> str:
    messages = {
        "db_ready": "База данных подготовлена",
        "employee_added": "Сотрудник добавлен",
        "item_added": "Материал добавлен",
        "batch_added": "Партия создана",
        "order_added": "Заказ добавлен",
    }
    return messages.get(code, code)

def layout(title: str, content: str, notice: str = "") -> str:
    return f"""<!doctype html>
<html lang='ru'>
<head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{title}</title>
<link rel='stylesheet' href='/static/styles.css'></head>
<body>
<header><h1>Автоматизация мороженого завода</h1>
<nav>
<a href='/'>Дашборд</a>
<a href='/employees'>Сотрудники</a>
<a href='/inventory'>Склад</a>
<a href='/batches'>Партии</a>
<a href='/orders'>Заказы</a>
</nav></header>
<main>{f"<div class='flash success'>{html.escape(notice)}</div>" if notice else ""}{content}</main>
</body></html>"""


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, text: str, status: int = 200) -> None:
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.end_headers()

    def _post_data(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw)
        return {k: v[0] for k, v in parsed.items()}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)

        if path == "/static/styles.css":
            css = STATIC_CSS_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.send_header("Content-Length", str(len(css)))
            self.end_headers()
            self.wfile.write(css)
            return

        if path == "/setup":
            init_db()
            seed_data()
            self._redirect("/?notice=db_ready")
            return

        notice = notice_text(query.get("notice", [""])[0])

        if path == "/":
            with db_conn() as conn:
                stats = {
                    "employees": conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0],
                    "inventory": conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0],
                    "batches": conn.execute("SELECT COUNT(*) FROM production_batches").fetchone()[0],
                    "orders": conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
                }
                low = conn.execute("SELECT item_name, quantity, unit, min_threshold FROM inventory WHERE quantity <= min_threshold").fetchall()
                recent = conn.execute("SELECT flavor, volume_liters, status, operator_name FROM production_batches ORDER BY id DESC LIMIT 5").fetchall()
            cards = "".join(f"<article class='card'><h3>{k}</h3><p>{v}</p></article>" for k, v in {
                "Сотрудники": stats["employees"], "Позиции склада": stats["inventory"], "Партии": stats["batches"], "Заказы": stats["orders"]
            }.items())
            low_rows = [
                [x["item_name"], f"{x['quantity']} {x['unit']}", f"{x['min_threshold']} {x['unit']}"]
                for x in low
            ] or [["Нет", "-", "-"]]
            recent_rows = [[x["flavor"], x["volume_liters"], x["status"], x["operator_name"]] for x in recent]
            content = (
                f"<section class='cards'>{cards}</section>"
                "<section class='panel-grid'>"
                f"<div class='panel'><h2>Критические остатки</h2>{table(['Материал','Остаток','Мин. порог'], low_rows)}</div>"
                f"<div class='panel'><h2>Последние партии</h2>{table(['Вкус','Объем','Статус','Оператор'], recent_rows)}</div>"
                "</section>"
            )
            self._send_html(layout("Дашборд", content, notice))
            return

        page_map = {
            "/employees": ("employees", "Сотрудники", ["ФИО", "Должность", "Смена", "Телефон"], "name, role, shift, phone"),
            "/inventory": ("inventory", "Склад", ["Материал", "Категория", "Количество", "Порог"], "item_name, category, quantity || ' ' || unit, min_threshold || ' ' || unit"),
            "/batches": ("production_batches", "Партии", ["Вкус", "Объем", "Статус", "Оператор", "Старт"], "flavor, volume_liters || ' л', status, operator_name, started_at"),
            "/orders": ("orders", "Заказы", ["Клиент", "Продукт", "Коробки", "Срок", "Статус"], "client_name, product, quantity_boxes, due_date, status"),
        }
        if path in page_map:
            table_name, title, headers, columns = page_map[path]
            with db_conn() as conn:
                rows = conn.execute(f"SELECT {columns} FROM {table_name} ORDER BY id DESC").fetchall()
            rows_data = [[row[i] for i in range(len(row))] for row in rows]
            form = self._form_for(path)
            content = f"<section class='form-section'><h2>Добавить запись</h2>{form}</section><section class='panel'><h2>{title}</h2>{table(headers, rows_data)}</section>"
            self._send_html(layout(title, content, notice))
            return

        self._send_html(layout("404", "<h2>Страница не найдена</h2>"), 404)

    def _form_for(self, path: str) -> str:
        forms = {
            "/employees": "<form method='post' class='grid-form'><input name='name' placeholder='ФИО' required><input name='role' placeholder='Должность' required><input name='shift' placeholder='Смена' required><input name='phone' placeholder='Телефон' required><button>Сохранить</button></form>",
            "/inventory": "<form method='post' class='grid-form'><input name='item_name' placeholder='Название' required><input name='category' placeholder='Категория' required><input name='quantity' type='number' step='0.01' placeholder='Количество' required><input name='unit' placeholder='Ед. изм.' required><input name='min_threshold' type='number' step='0.01' placeholder='Мин. порог' required><button>Добавить</button></form>",
            "/batches": "<form method='post' class='grid-form'><input name='flavor' placeholder='Вкус' required><input name='volume_liters' type='number' step='0.01' placeholder='Объем (л)' required><input name='operator_name' placeholder='Оператор' required><select name='status'><option>Новый</option><option>В процессе</option><option>Завершено</option></select><button>Создать</button></form>",
            "/orders": "<form method='post' class='grid-form'><input name='client_name' placeholder='Клиент' required><input name='product' placeholder='Продукт' required><input name='quantity_boxes' type='number' placeholder='Коробки' required><input name='due_date' type='date' required><select name='status'><option>Новый</option><option>В сборке</option><option>Отгружен</option></select><button>Сохранить</button></form>",
        }
        return forms[path]

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        data = self._post_data()
        with db_conn() as conn:
            if path == "/employees":
                conn.execute("INSERT INTO employees(name, role, shift, phone) VALUES (?, ?, ?, ?)", (data["name"], data["role"], data["shift"], data["phone"]))
                self._redirect("/employees?notice=employee_added")
                return
            if path == "/inventory":
                conn.execute("INSERT INTO inventory(item_name, category, quantity, unit, min_threshold) VALUES (?, ?, ?, ?, ?)", (data["item_name"], data["category"], float(data["quantity"]), data["unit"], float(data["min_threshold"])))
                self._redirect("/inventory?notice=item_added")
                return
            if path == "/batches":
                conn.execute("INSERT INTO production_batches(flavor, volume_liters, status, operator_name, started_at) VALUES (?, ?, ?, ?, ?)", (data["flavor"], float(data["volume_liters"]), data["status"], data["operator_name"], datetime.now().strftime("%Y-%m-%d %H:%M")))
                self._redirect("/batches?notice=batch_added")
                return
            if path == "/orders":
                conn.execute("INSERT INTO orders(client_name, product, quantity_boxes, due_date, status) VALUES (?, ?, ?, ?, ?)", (data["client_name"], data["product"], int(data["quantity_boxes"]), data["due_date"], data["status"]))
                self._redirect("/orders?notice=order_added")
                return
        self._send_html(layout("Ошибка", "<h2>Некорректный POST</h2>"), 400)


if __name__ == "__main__":
    if not DB_PATH.exists():
        init_db()
        seed_data()
    server = ThreadingHTTPServer(("0.0.0.0", 5000), Handler)
    print("Server started at http://127.0.0.1:5000")
    server.serve_forever()
