# syntax=docker/dockerfile:1
FROM python:3.13-slim

# System deps needed by asyncpg / psycopg2 build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (cached layer — only rebuilt when requirements change)
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# Copy full project (app/, alembic/, entrypoint.sh, alembic.ini)
COPY . .

EXPOSE 8000

ENTRYPOINT ["sh", "entrypoint.sh"]
