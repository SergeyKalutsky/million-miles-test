"""
Scraper Docker entry-point — called by cron every hour.

ENV vars:
    SCRAPER_LIVE=1      → fetch from the real network  (default: 0 = offline)
    DATABASE_URL        → set by docker-compose via .env
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Ensure project root is importable (/app in container)
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_here, "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scraper.save_to_db import main  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)

if __name__ == "__main__":
    live = os.getenv("SCRAPER_LIVE", "0") == "1"
    asyncio.run(main(live=live))
