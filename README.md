# IceFactory ERP — Автоматизация деятельности мороженого завода

Готовый веб-сайт для управления мороженым заводом с базой данных **PostgreSQL**.

## Возможности
- Дашборд с KPI;
- Учет сотрудников;
- Склад сырья и упаковки;
- Производственные партии;
- Заказы клиентов.

## Стек
- Python 3
- `http.server`
- PostgreSQL
- `psycopg` (PostgreSQL драйвер)

## 1) Поднять PostgreSQL (пример через Docker)
```bash
docker run --name icefactory-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=icefactory \
  -p 5432:5432 -d postgres:16
```

## 2) Установить зависимости и запустить сайт
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/icefactory'
python3 app.py
```

После запуска откройте `http://127.0.0.1:5000`.

## Переинициализация данных
- Перейдите на `http://127.0.0.1:5000/setup`
- Будет повторно применена схема из `schema.sql` и стартовые данные.

## Структура
- `app.py` — web backend и CRUD-маршруты;
- `schema.sql` — схема PostgreSQL;
- `static/styles.css` — стили интерфейса.
