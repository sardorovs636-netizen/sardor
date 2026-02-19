# IceFactory ERP/MES — Автоматизация мороженого завода

Готовый веб-сайт для внедрения **ERP** и **MES** процессов на мороженом заводе (PostgreSQL).

## Что уже внедрено
### ERP блок
- Заказы клиентов;
- Закупки и снабжение (`ERP` раздел);
- Склад сырья и упаковки;
- Базовый контроль бюджета закупок и поставок в пути.

### MES блок
- Учет производственных партий;
- События производственной линии (`MES` раздел): простой, наладка, плановый выпуск, брак;
- KPI MES на дашборде: среднее качество и суммарные простои.

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
- Будет повторно применена схема и стартовые ERP/MES данные.

## Структура
- `app.py` — web backend и модули ERP/MES;
- `schema.sql` — схема PostgreSQL;
- `static/styles.css` — стили интерфейса.
