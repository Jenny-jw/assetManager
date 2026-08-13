from __future__ import annotations

from uuid import UUID

from fastapi import Depends

from dependencies.auth import require_tenant_id
from dependencies.db import DbSession
from repositories.postgres.stock_repository import StockRepository

def get_stock_repository(
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
) -> StockRepository:
    return StockRepository(db, tenant_id=tenant_id)