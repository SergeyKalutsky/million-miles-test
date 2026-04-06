from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, cars


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup (dev convenience).
    # In production use Alembic migrations instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
