"""
Scraper entry-point for the Docker container.
Runs once immediately on startup, then repeats every hour.

ENV vars:
    SCRAPER_LIVE=1      → fetch from the real network  (default: 0 = offline)
    SCRAPER_INTERVAL=3600  → seconds between runs (default: 3600)
    DATABASE_URL        → set by docker-compose via .env
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

# Ensure project root (/app) is importable
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_here, "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scraper.save_to_db import main  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

INTERVAL = int(os.getenv("SCRAPER_INTERVAL", "3600"))

if __name__ == "__main__":
    live = os.getenv("SCRAPER_LIVE", "0") == "1"
    log.info("Scraper starting — live=%s, interval=%ds", live, INTERVAL)
    while True:
        log.info("=== Scraper run starting ===")
        try:
            asyncio.run(main(live=live))
        except Exception as exc:
            log.error("Scraper run failed: %s", exc, exc_info=True)
        log.info("=== Scraper run done. Next run in %ds ===", INTERVAL)
        time.sleep(INTERVAL)
