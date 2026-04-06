from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


# ---------------------------------------------------------------------------
# Cars
# ---------------------------------------------------------------------------

class CarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    source_url: str
    brand: str | None
    model: str | None
    body_type: str | None
    fuel_type: str | None
    transmission: str | None
    color: str | None
    year: int | None
    mileage_km: int | None
    price_jpy: int | None
    location: str | None
    photos: list[str] | None
    created_at: datetime
    updated_at: datetime


class CarUpsert(BaseModel):
    """Used by the scraper to push data into the DB."""

    external_id: str
    source_url: str
    brand: str | None = None
    model: str | None = None
    body_type: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    color: str | None = None
    year: int | None = None
    mileage_km: int | None = None
    price_jpy: int | None = None
    location: str | None = None
    photos: list[str] | None = None
    raw_json: dict[str, Any] | None = None
    raw_text: str | None = None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PaginatedCars(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    items: list[CarOut]
