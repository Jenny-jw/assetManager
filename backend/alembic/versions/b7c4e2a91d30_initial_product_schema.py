"""initial product schema

Revision ID: b7c4e2a91d30
Revises:
Create Date: 2026-06-16 16:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b7c4e2a91d30"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            server_default=sa.text("'owner'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('owner')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "stocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("genre", sa.String(length=50), nullable=True),
        sa.Column("origin", sa.String(length=100), nullable=True),
        sa.Column("producer", sa.String(length=200), nullable=True),
        sa.Column("roast_level", sa.SmallInteger(), nullable=True),
        sa.Column("harvest_time", sa.Integer(), nullable=True),
        sa.Column("weight_grams", sa.Integer(), nullable=True),
        sa.Column(
            "quantity",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("score", sa.SmallInteger(), nullable=True),
        sa.Column("price_per_jin", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "roast_level IS NULL OR (roast_level >= 0 AND roast_level <= 100)",
            name="ck_stocks_roast_level",
        ),
        sa.CheckConstraint(
            "harvest_time IS NULL OR (harvest_time >= 20100101 AND harvest_time <= 22001231)",
            name="ck_stocks_harvest_time",
        ),
        sa.CheckConstraint(
            "weight_grams IS NULL OR weight_grams > 0",
            name="ck_stocks_weight_grams",
        ),
        sa.CheckConstraint("quantity >= 0", name="ck_stocks_quantity"),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_stocks_score",
        ),
        sa.CheckConstraint(
            "price_per_jin IS NULL OR price_per_jin >= 0",
            name="ck_stocks_price_per_jin",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stocks_genre", "stocks", ["genre"], unique=False)
    op.create_index("ix_stocks_origin", "stocks", ["origin"], unique=False)
    op.create_index(
        "ix_stocks_active",
        "stocks",
        ["deleted_at"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

def downgrade() -> None:
    op.drop_index("ix_stocks_active", table_name="stocks")
    op.drop_index("ix_stocks_origin", table_name="stocks")
    op.drop_index("ix_stocks_genre", table_name="stocks")
    op.drop_table("stocks")
    op.drop_table("users")
