from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base

if TYPE_CHECKING:
    from models.tenant import Tenant

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('owner')", name="ck_users_role"),
        UniqueConstraint(
            "tenant_id",
            "username",
            name="uq_users_tenant_username",
        ),
        UniqueConstraint(
            "tenant_id",
            "email",
            name="uq_users_tenant_email",
        ),
        Index(
            "uq_users_one_owner_per_tenant",
            "tenant_id",
            unique=True,
            postgresql_where=text("role = 'owner'"),
            sqlite_where=text("role = 'owner'"),
        ),
        Index("ix_users_tenant_id", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=True,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'owner'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
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

    tenant: Mapped[Tenant | None] = relationship(back_populates="users")