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
from app.database import Base  # noqa: E402

from scraper.parser import CarDetail, run_scraper  # noqa: E402

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")


async def upsert_car(session: AsyncSession, car: CarDetail) -> None:
    data = asdict(car)
    result = await session.execute(select(Car).where(Car.external_id == car.external_id))
    existing = result.scalar_one_or_none()
    if existing is None:
        session.add(Car(**data))
        log.info("  INSERT  %s  %s %s", car.external_id, car.brand, car.model)
    else:
        for k, v in data.items():
            setattr(existing, k, v)
        log.info("  UPDATE  %s  %s %s", car.external_id, car.brand, car.model)


async def main(live: bool) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cars = run_scraper(live=live)
    log.info("Saving %d cars to DB …", len(cars))

    async with AsyncSessionLocal() as session:
        for car in cars:
            await upsert_car(session, car)
        await session.commit()

    log.info("Done.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main(live="--live" in sys.argv))
