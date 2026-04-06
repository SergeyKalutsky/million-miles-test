# Million Miles — CarSensor.net scraper + API

## Stack

| Component | Tech |
|-----------|------|
| Database  | PostgreSQL 16 |
| API       | FastAPI + SQLAlchemy 2 (async) + asyncpg |
| Migrations| Alembic |
| Auth      | JWT (python-jose + passlib/bcrypt) |
| Scraper   | requests + BeautifulSoup 4 |
| Runtime   | Docker Compose |

---

## Quick start

```bash
# 1. Copy env template
cp .env.example .env        # then edit secrets if needed

# 2. Start DB + API (migrations run automatically on api startup)
docker compose up --build -d

# 3. Check API is healthy
curl http://localhost:8000/health

# 4. Browse interactive docs
open http://localhost:8000/docs
```

---

## Scraper

```bash
# Offline mode — parses local outer.html + detail.html (no network)
docker compose run --rm scraper

# Live mode — fetches 10 listing pages + all detail pages from carsensor.net
SCRAPER_LIVE=1 docker compose run --rm scraper
```

Or run directly without Docker:

```bash
python run_scraper.py          # offline
SCRAPER_LIVE=1 python run_scraper.py   # live
```

---

## API endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT token (OAuth2 form) |
| GET  | `/auth/me` | Current user info |

### Cars (all require `Authorization: Bearer <token>`)

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/cars/` | List with filters, sort, pagination |
| GET  | `/cars/{id}` | Single car |
| POST | `/cars/upsert` | Insert/update car (used by scraper) |

#### `/cars/` query parameters

| Param | Type | Example |
|-------|------|---------|
| `brand` | string | `Toyota` |
| `model` | string (partial) | `Serena` |
| `body_type` | string | `SUV` |
| `fuel_type` | string | `hybrid` |
| `transmission` | string | `CVT` |
| `location` | string (partial) | `埼玉` |
| `year_min` / `year_max` | int | `2018` / `2023` |
| `price_min` / `price_max` | int (JPY) | `500000` / `3000000` |
| `mileage_max` | int (km) | `50000` |
| `sort_by` | `price_jpy` \| `mileage_km` \| `year` \| `created_at` | `price_jpy` |
| `order` | `asc` \| `desc` | `asc` |
| `page` | int ≥1 | `1` |
| `page_size` | int 1–100 | `20` |

---

## Migrations

```bash
# Generate a new migration after model changes
docker compose exec api alembic revision --autogenerate -m "add column X"

# Apply
docker compose exec api alembic upgrade head

# Rollback one step
docker compose exec api alembic downgrade -1
```

---

## Project structure

```
.
├── app/
│   ├── main.py          # FastAPI app, lifespan
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # Async engine + session
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── security.py      # JWT + bcrypt helpers
│   ├── deps.py          # FastAPI dependencies (current_user)
│   └── routers/
│       ├── auth.py      # /auth/*
│       └── cars.py      # /cars/*
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── parser.py            # Scraper logic (listings + detail pages)
├── save_to_db.py        # Scraper → DB bridge
├── run_scraper.py       # Docker entrypoint for scraper container
├── Dockerfile           # API image
├── Dockerfile.scraper   # Scraper image
├── entrypoint.sh        # API startup: wait-for-db → migrate → uvicorn
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── .env.example
```
