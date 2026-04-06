"""
Bridge: run the scraper and write results directly into Postgres via SQLAlchemy.

Usage (inside container or venv):
    python save_to_db.py           # offline mode (local HTML files)
    python save_to_db.py --live    # live scrape
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# ── resolve DATABASE_URL ──────────────────────────────────────────────────────
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://mm:mm_secret@localhost:5432/million_miles",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# ── import Car model (app package must be on the path) ────────────────────────
# When running from /scraper inside container, /app is the project root
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_here, "..")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.models import Car  # noqa: E402  (after sys.path fixup)

from scraper.parser import CarDetail, run_scraper  # noqa: E402

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")


async def get_known_ids(session: AsyncSession) -> set[str]:
    """Return the set of external_ids already stored in the DB."""
    result = await session.execute(select(Car.external_id))
    return {row[0] for row in result.fetchall()}


async def insert_car(session: AsyncSession, car: CarDetail) -> None:
    """Insert a brand-new car and commit immediately."""
    session.add(Car(**asdict(car)))
    await session.commit()
    log.info("  SAVED  %s  %s %s", car.external_id, car.brand, car.model)


async def main(live: bool) -> None:
    async with AsyncSessionLocal() as session:
        known_ids = await get_known_ids(session)
    log.info("DB already contains %d cars — will skip those.", len(known_ids))

    async with AsyncSessionLocal() as session:

        async def save_callback(car: CarDetail) -> None:
            """Called by the scraper right after each detail page is parsed."""
            await insert_car(session, car)

        await run_scraper(live=live, known_ids=known_ids, on_car_saved=save_callback)

    log.info("Done.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(live="--live" in sys.argv))
