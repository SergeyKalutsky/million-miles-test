# syntax=docker/dockerfile:1
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install scraper deps first (layer cache)
COPY scraper/requirements.txt scraper/requirements.txt
RUN pip install --no-cache-dir -r scraper/requirements.txt

# Install app deps (scraper imports app.models / app.database / app.security)
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

# Copy full project so app.* imports resolve
COPY . .

# Run once immediately, then loop every SCRAPER_INTERVAL seconds (default 3600)
CMD ["python", "scraper/run_scraper.py"]
