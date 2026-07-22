from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, JSON, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.stock import Stock
    from models.user import User

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "edition IN ('personal', 'professional')",
            name="ck_tenants_edition",
        ),
        CheckConstraint(
            "locale IN ('zh-TW', 'en')",
            name="ck_tenants_locale",
        ),
        CheckConstraint(
            "status IN ('trial', 'active', 'suspended')",
            name="ck_tenants_status",
        ),
        CheckConstraint(
            "status != 'trial' OR trial_ends_at IS NOT NULL",
            name="ck_tenants_trial_has_end",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    edition: Mapped[str] = mapped_column(String(20), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    roles_enabled: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
    )
    modules: Mapped[dict[str, bool]] = mapped_column(
        MutableDict.as_mutable(JSON),
        nullable=False,
    )
    dashboard_layout: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'trial'"),
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    users: Mapped[list[User]] = relationship(back_populates="tenant")
    stocks: Mapped[list[Stock]] = relationship(back_populates="tenant")
