from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.tenant import Tenant

class Stock(Base):
    __tablename__ = "stocks"
    __table_args__ = (
        CheckConstraint(
            "roast_level IS NULL OR (roast_level >= 0 AND roast_level <= 100)",
            name="ck_stocks_roast_level",
        ),
        CheckConstraint(
            "harvest_time IS NULL OR (harvest_time >= 20100101 AND harvest_time <= 22001231)",
            name="ck_stocks_harvest_time",
        ),
        CheckConstraint(
            "weight_grams IS NULL OR weight_grams > 0",
            name="ck_stocks_weight_grams",
        ),
        CheckConstraint("quantity >= 0", name="ck_stocks_quantity"),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_stocks_score",
        ),
        CheckConstraint(
            "price_per_jin IS NULL OR price_per_jin >= 0",
            name="ck_stocks_price_per_jin",
        ),
        Index("ix_stocks_tenant_id", "tenant_id"),
        Index("ix_stocks_genre", "genre"),
        Index("ix_stocks_origin", "origin"),
        Index(
            "ix_stocks_active",
            "deleted_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[str | None] = mapped_column(String(50), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    producer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    roast_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    harvest_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    price_per_jin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    tenant: Mapped[Tenant] = relationship(back_populates="stocks")