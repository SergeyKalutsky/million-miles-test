"""Initial schema: users + cars tables

Revision ID: 0001
Revises:
Create Date: 2026-04-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users -----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- cars ------------------------------------------------------------
    op.create_table(
        "cars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("brand", sa.String(128)),
        sa.Column("model", sa.String(256)),
        sa.Column("body_type", sa.String(64)),
        sa.Column("fuel_type", sa.String(32)),
        sa.Column("transmission", sa.String(32)),
        sa.Column("color", sa.String(64)),
        sa.Column("year", sa.Integer()),
        sa.Column("mileage_km", sa.Integer()),
        sa.Column("price_jpy", sa.BigInteger()),
        sa.Column("location", sa.String(128)),
        sa.Column("photos", postgresql.ARRAY(sa.Text())),
        sa.Column("raw_json", postgresql.JSONB()),
        sa.Column("raw_text", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("external_id", name="uq_cars_external_id"),
    )
    op.create_index("ix_cars_external_id", "cars", ["external_id"])
    op.create_index("ix_cars_brand", "cars", ["brand"])
    op.create_index("ix_cars_model", "cars", ["model"])
    op.create_index("ix_cars_year", "cars", ["year"])
    op.create_index("ix_cars_price_jpy", "cars", ["price_jpy"])
    op.create_index("ix_cars_mileage_km", "cars", ["mileage_km"])
    op.create_index("ix_cars_location", "cars", ["location"])
    op.create_index("ix_cars_body_type", "cars", ["body_type"])
    op.create_index("ix_cars_fuel_type", "cars", ["fuel_type"])

    # Auto-update updated_at on every row change
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_cars_updated_at
        BEFORE UPDATE ON cars
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_cars_updated_at ON cars;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")
    op.drop_table("cars")
    op.drop_table("users")
