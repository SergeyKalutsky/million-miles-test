#!/bin/sh
# entrypoint.sh — runs inside the `api` container.
# 1. Wait for Postgres to be ready
# 2. Run Alembic migrations
# 3. Start uvicorn

set -e

echo "==> Waiting for Postgres…"
until python - <<'EOF'
import asyncio, asyncpg, os, sys
async def check():
    try:
        # asyncpg uses the raw postgres:// URL, strip the +asyncpg driver prefix
        url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url, timeout=3)
        await conn.close()
    except Exception as e:
        sys.exit(1)
asyncio.run(check())
EOF
do
  echo "   Postgres not ready, retrying in 2s…"
  sleep 2
done
echo "==> Postgres is up."

echo "==> Running Alembic migrations…"
alembic upgrade head

echo "==> Starting API server…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
