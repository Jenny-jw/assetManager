"""contract tenant_id not null

Revision ID: d2064bf95049
Revises: 8f3a1c7d2e4b
Create Date: 2026-07-30 12:00:00.000000

"""
from __future__ import annotations

import json
from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d2064bf95049"
down_revision: Union[str, None] = "8f3a1c7d2e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BOOTSTRAP_SLUG = "legacy-bootstrap"

_BOOTSTRAP_MODULES = {
    "inventory": True,
    "dashboard_summary": True,
    "dashboard_origin_chart": True,
    "dashboard_genre_chart": True,
    "dashboard_recent_assets": True,
    "orders": False,
    "order_notifications": False,
    "pricing_visibility": True,
    "profit_analytics": False,
}

_BOOTSTRAP_LAYOUT = ["summary", "origin", "genre", "recent_assets"]

def _null_tenant_count(connection, table_name: str) -> int:
    return int(
        connection.execute(
            sa.text(f"SELECT count(*) FROM {table_name} WHERE tenant_id IS NULL")
        ).scalar_one()
    )

def _backfill_orphan_tenant_ids(connection) -> None:
    orphan_users = _null_tenant_count(connection, "users")
    orphan_stocks = _null_tenant_count(connection, "stocks")
    if orphan_users == 0 and orphan_stocks == 0:
        return

    tenant_rows = connection.execute(
        sa.text("SELECT id FROM tenants ORDER BY created_at ASC, id ASC")
    ).fetchall()

    if len(tenant_rows) == 1:
        target_id = tenant_rows[0][0]
    elif len(tenant_rows) == 0:
        target_id = uuid4()
        connection.execute(
            sa.text(
                """
                INSERT INTO tenants (
                    id,
                    slug,
                    edition,
                    locale,
                    roles_enabled,
                    modules,
                    dashboard_layout,
                    status
                )
                VALUES (
                    :id,
                    :slug,
                    'personal',
                    'zh-TW',
                    CAST(:roles AS json),
                    CAST(:modules AS json),
                    CAST(:layout AS json),
                    'active'
                )
                """
            ),
            {
                "id": str(target_id),
                "slug": _BOOTSTRAP_SLUG,
                "roles": json.dumps(["owner"]),
                "modules": json.dumps(_BOOTSTRAP_MODULES),
                "layout": json.dumps(_BOOTSTRAP_LAYOUT),
            },
        )
    else:
        raise RuntimeError(
            "Cannot contract tenant_id: "
            f"{orphan_users} users and {orphan_stocks} stocks still have NULL "
            f"tenant_id while {len(tenant_rows)} tenants exist. "
            "Assign ownership manually, then re-run the migration."
        )

    connection.execute(
        sa.text("UPDATE users SET tenant_id = :tid WHERE tenant_id IS NULL"),
        {"tid": str(target_id)},
    )
    connection.execute(
        sa.text("UPDATE stocks SET tenant_id = :tid WHERE tenant_id IS NULL"),
        {"tid": str(target_id)},
    )

def upgrade() -> None:
    connection = op.get_bind()
    _backfill_orphan_tenant_ids(connection)

    remaining_users = _null_tenant_count(connection, "users")
    remaining_stocks = _null_tenant_count(connection, "stocks")
    if remaining_users or remaining_stocks:
        raise RuntimeError(
            "Cannot contract tenant_id: "
            f"{remaining_users} users and {remaining_stocks} stocks still have "
            "NULL tenant_id after backfill."
        )

    op.alter_column(
        "users",
        "tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.alter_column(
        "stocks",
        "tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

def downgrade() -> None:
    op.alter_column(
        "stocks",
        "tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.alter_column(
        "users",
        "tenant_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )