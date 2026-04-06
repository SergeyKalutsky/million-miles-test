from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, engine
from app.models import User
from app.routers import auth, cars
from app.security import hash_password

log = logging.getLogger(__name__)


async def _seed_admin() -> None:
    """Create admin:admin123 if not present."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none() is None:
            session.add(
                User(
                    username="admin",
                    email="admin@million-miles.local",
                    hashed_password=hash_password("admin123"),
                    is_active=True,
                )
            )
            await session.commit()
            log.info("Admin user created (admin / admin123)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created by Alembic in entrypoint.sh — don't call create_all here.
    await _seed_admin()
    yield
    await engine.dispose()


app = FastAPI(
    title="Million Miles API",
    version="0.1.0",
    description="Used car listings from carsensor.net",
    lifespan=lifespan,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cars.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
