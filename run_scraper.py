"""
Scraper entry-point for the Docker container.

ENV vars:
    SCRAPER_LIVE=1          → fetch from the real network (default: offline)
    DATABASE_URL            → overridden by compose via .env
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Make sure app/ is importable when running from project root
sys.path.insert(0, "/app")

from save_to_db import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)

if __name__ == "__main__":
    live = os.getenv("SCRAPER_LIVE", "0") == "1"
    asyncio.run(main(live=live))
