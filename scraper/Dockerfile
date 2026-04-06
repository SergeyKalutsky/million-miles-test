# syntax=docker/dockerfile:1
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install scraper Python deps
COPY scraper/requirements.txt scraper/requirements.txt
RUN pip install --no-cache-dir -r scraper/requirements.txt

# Install app deps too (for SQLAlchemy models / DB access)
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# Copy entire project so scraper can import app.models, app.database, etc.
COPY . .

# Install crontab
RUN crontab scraper/crontab

# On startup: run scraper once immediately, then hand off to cron
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["python scraper/run_scraper.py; cron -f"]
