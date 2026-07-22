"""add tenant foundation

Revision ID: 8f3a1c7d2e4b
Revises: b7c4e2a91d30
Create Date: 2026-07-21 08:45:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8f3a1c7d2e4b"
down_revision: Union[str, None] = "b7c4e2a91d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("edition", sa.String(length=20), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("roles_enabled", sa.JSON(), nullable=False),
        sa.Column("modules", sa.JSON(), nullable=False),
        sa.Column("dashboard_layout", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'trial'"),
            nullable=False,
        ),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "edition IN ('personal', 'professional')",
            name="ck_tenants_edition",
        ),
        sa.CheckConstraint(
            "locale IN ('zh-TW', 'en')",
            name="ck_tenants_locale",
        ),
        sa.CheckConstraint(
            "status IN ('trial', 'active', 'suspended')",
            name="ck_tenants_status",
        ),
        sa.CheckConstraint(
            "status != 'trial' OR trial_ends_at IS NOT NULL",
            name="ck_tenants_trial_has_end",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.add_column(
        "users",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "stocks",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_tenant_id_tenants",
        "users",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_stocks_tenant_id_tenants",
        "stocks",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint("users_username_key", "users", type_="unique")
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_unique_constraint(
        "uq_users_tenant_username",
        "users",
        ["tenant_id", "username"],
    )
    op.create_unique_constraint(
        "uq_users_tenant_email",
        "users",
        ["tenant_id", "email"],
    )
    op.create_index(
        "uq_users_one_owner_per_tenant",
        "users",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("role = 'owner'"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], unique=False)
    op.create_index("ix_stocks_tenant_id", "stocks", ["tenant_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_stocks_tenant_id", table_name="stocks")
    op.drop_index("ix_users_tenant_id", table_name="users")
    op.drop_index("uq_users_one_owner_per_tenant", table_name="users")
    op.drop_constraint("uq_users_tenant_email", "users", type_="unique")
    op.drop_constraint("uq_users_tenant_username", "users", type_="unique")
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.create_unique_constraint("users_username_key", "users", ["username"])
    op.drop_constraint(
        "fk_stocks_tenant_id_tenants",
        "stocks",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_users_tenant_id_tenants",
        "users",
        type_="foreignkey",
    )
    op.drop_column("stocks", "tenant_id")
    op.drop_column("users", "tenant_id")
    op.drop_table("tenants")
