from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import CurrentUser
from app.models import Car
from app.schemas import CarOut, CarUpsert, PaginatedCars

router = APIRouter(prefix="/cars", tags=["cars"])


# ---------------------------------------------------------------------------
# Sortable columns whitelist
# ---------------------------------------------------------------------------

class SortField(str, Enum):
    price_jpy = "price_jpy"
    mileage_km = "mileage_km"
    year = "year"
    created_at = "created_at"


# ---------------------------------------------------------------------------
# GET /cars  — list with filters, sort, pagination
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedCars)
async def list_cars(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,  # require auth
    # --- filters ---
    brand: str | None = Query(None, description="Filter by brand (exact, case-insensitive)"),
    model: str | None = Query(None, description="Filter by model (partial match)"),
    body_type: str | None = Query(None),
    fuel_type: str | None = Query(None),
    transmission: str | None = Query(None),
    location: str | None = Query(None, description="Filter by prefecture (partial match)"),
    year_min: int | None = Query(None, ge=1950),
    year_max: int | None = Query(None, le=2100),
    price_min: int | None = Query(None, ge=0, description="Min price in JPY"),
    price_max: int | None = Query(None, ge=0, description="Max price in JPY"),
    mileage_max: int | None = Query(None, ge=0, description="Max mileage in km"),
    # --- sort ---
    sort_by: SortField = Query(SortField.created_at),
    order: Literal["asc", "desc"] = Query("desc"),
    # --- pagination ---
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedCars:
    """
    Return paginated list of cars.
    All filters are optional and combinable.
    Requires a valid JWT token.
    """
    stmt: Select = select(Car)

    # --- apply filters ---
    if brand:
        stmt = stmt.where(func.lower(Car.brand) == brand.lower())
    if model:
        stmt = stmt.where(Car.model.ilike(f"%{model}%"))
    if body_type:
        stmt = stmt.where(func.lower(Car.body_type) == body_type.lower())
    if fuel_type:
        stmt = stmt.where(func.lower(Car.fuel_type) == fuel_type.lower())
    if transmission:
        stmt = stmt.where(func.lower(Car.transmission) == transmission.lower())
    if location:
        stmt = stmt.where(Car.location.ilike(f"%{location}%"))
    if year_min is not None:
        stmt = stmt.where(Car.year >= year_min)
    if year_max is not None:
        stmt = stmt.where(Car.year <= year_max)
    if price_min is not None:
        stmt = stmt.where(Car.price_jpy >= price_min)
    if price_max is not None:
        stmt = stmt.where(Car.price_jpy <= price_max)
    if mileage_max is not None:
        stmt = stmt.where(Car.mileage_km <= mileage_max)

    # --- count total (before pagination) ---
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    # --- apply sort ---
    sort_col = getattr(Car, sort_by.value)
    stmt = stmt.order_by(desc(sort_col) if order == "desc" else asc(sort_col))

    # --- apply pagination ---
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    rows = (await db.execute(stmt)).scalars().all()

    return PaginatedCars(
        total=total,
        page=page,
        page_size=page_size,
        items=[CarOut.model_validate(r) for r in rows],
    )


# ---------------------------------------------------------------------------
# GET /cars/{id}
# ---------------------------------------------------------------------------

@router.get("/{car_id}", response_model=CarOut)
async def get_car(
    car_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
) -> Car:
    """Return a single car by internal ID. Requires auth."""
    car = await db.get(Car, car_id)
    if car is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found.")
    return car


# ---------------------------------------------------------------------------
# POST /cars/upsert  — internal endpoint used by the scraper
# ---------------------------------------------------------------------------

@router.post("/upsert", response_model=CarOut, status_code=201)
async def upsert_car(
    body: CarUpsert,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: CurrentUser,
) -> Car:
    """
    Insert or update a car by external_id.
    Used by the scraper after parsing each detail page.
    """
    result = await db.execute(select(Car).where(Car.external_id == body.external_id))
    car = result.scalar_one_or_none()

    data = body.model_dump()
    if car is None:
        car = Car(**data)
        db.add(car)
    else:
        for k, v in data.items():
            setattr(car, k, v)

    await db.flush()
    await db.refresh(car)
    return car
