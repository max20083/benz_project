# АЗС «Бенз»

Симулятор занятия колонки. На экране выбираются колонка, топливо, тариф и объём в литрах или рублях. FastAPI считает цену и пишет сессию в SQLite, React показывает табло: около 1,8 л/с, пока заправка не закончится или её не остановят.

Справочники при первом запуске:

| Топливо | Цена |
| --- | --- |
| АИ-92 | 54,90 ₽/л |
| АИ-95 | 59,40 ₽/л |
| АИ-98 | 68,20 ₽/л |
| ДТ | 62,10 ₽/л |

Тарифы: базовый, карта −5%, ночной −8%. Колонки: 1–4.

## Запуск

Нужны два терминала. Из корня репозитория:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Интерфейс: http://127.0.0.1:5173  
Документация API: http://127.0.0.1:8000/docs

## Сборка интерфейса

```bash
cd frontend
npm install
npm run build
npm run preview
```

`npm run build` кладёт статику в `frontend/dist`. `npm run preview` поднимает её локально. Бэкенд при этом должен работать на порту 8000: в режиме разработки Vite проксирует `/api` туда же. Для preview прокси нет, поэтому запросы интерфейса к `/api` сработают, если раздавать `dist` через тот же процесс, что и API, либо открывать страницу через `npm run dev`.

## База SQLite

Файл появляется при старте бэкенда:

`backend/data/station.db`

Посмотреть из корня репозитория:

```bash
sqlite3 backend/data/station.db
```

Внутри консоли:

```sql
.tables
.headers on
.mode column
SELECT * FROM fuels;
SELECT * FROM tariffs;
SELECT * FROM pumps;
SELECT id, pump_id, fuel_id, tariff_id, mode, status,
       dispensed_liters, target_total, started_at
FROM fueling_sessions
ORDER BY id DESC;
```

Одной командой, без входа в консоль:

```bash
sqlite3 -header -column backend/data/station.db \
  "SELECT id, status, dispensed_liters, target_total FROM fueling_sessions;"
```
