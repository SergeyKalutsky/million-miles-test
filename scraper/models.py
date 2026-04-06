"""
Data models for the scraper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ListingPreview:
    detail_url: str
    image: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CarDetail:
    external_id: str
    source_url: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    price_jpy: Optional[int] = None
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    body_type: Optional[str] = None
    color: Optional[str] = None
    location: Optional[str] = None
    photos: list[str] = field(default_factory=list)
    raw_json: Optional[dict] = None
    raw_text: Optional[str] = None
