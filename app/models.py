from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Application users (for JWT auth)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Car(Base):
    """Scraped car listings."""

    __tablename__ = "cars"
    __table_args__ = (UniqueConstraint("external_id", name="uq_cars_external_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- identity ---
    external_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    # --- classification ---
    brand: Mapped[str | None] = mapped_column(String(128), index=True)
    model: Mapped[str | None] = mapped_column(String(256), index=True)
    body_type: Mapped[str | None] = mapped_column(String(64), index=True)
    fuel_type: Mapped[str | None] = mapped_column(String(32), index=True)
    transmission: Mapped[str | None] = mapped_column(String(32))
    color: Mapped[str | None] = mapped_column(String(64))

    # --- numeric specs ---
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer, index=True)
    price_jpy: Mapped[int | None] = mapped_column(BigInteger, index=True)

    # --- location ---
    location: Mapped[str | None] = mapped_column(String(128), index=True)

    # --- media ---
    photos: Mapped[list[str] | None] = mapped_column(ARRAY(Text))

    # --- raw data ---
    raw_json: Mapped[dict | None] = mapped_column(JSONB)
    raw_text: Mapped[str | None] = mapped_column(Text)

    # --- timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
