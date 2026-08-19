"""add stock cost_per_jin for profit analytics

Revision ID: e1a7b9c04d18
Revises: c9e2f4a81b07
Create Date: 2026-08-15 15:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e1a7b9c04d18"
down_revision: str | None = "c9e2f4a81b07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("stocks", sa.Column("cost_per_jin", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_stocks_cost_per_jin",
        "stocks",
        "cost_per_jin IS NULL OR cost_per_jin >= 0",
    )

def downgrade() -> None:
    op.drop_constraint("ck_stocks_cost_per_jin", "stocks", type_="check")
    op.drop_column("stocks", "cost_per_jin")