"""
Bridge: run the scraper and write results directly into Postgres via SQLAlchemy
(bypasses the HTTP API — useful for batch import).

Usage:
    python save_to_db.py           # offline mode (local HTML files)
    python save_to_db.py --live    # live scrape
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# bootstrap app models so Base.metadata is populated
from app.database import AsyncSessionLocal, Base, engine
from app.models import Car
from parser import CarDetail, run_scraper

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")


async def upsert_car(session: AsyncSession, car: CarDetail) -> None:
    data = asdict(car)
    # raw_json is a dict — keep as-is (JSONB)
    # SQLAlchemy ARRAY(Text) expects a plain Python list — already fine

    result = await session.execute(select(Car).where(Car.external_id == car.external_id))
    existing = result.scalar_one_or_none()

    if existing is None:
        obj = Car(**data)
        session.add(obj)
        log.info("  INSERT  %s  %s %s", car.external_id, car.brand, car.model)
    else:
        for k, v in data.items():
            setattr(existing, k, v)
        log.info("  UPDATE  %s  %s %s", car.external_id, car.brand, car.model)


async def main(live: bool) -> None:
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cars = run_scraper(live=live)
    log.info("Saving %d cars to DB …", len(cars))

    async with AsyncSessionLocal() as session:
        for car in cars:
            await upsert_car(session, car)
        await session.commit()

    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main(live="--live" in sys.argv))
