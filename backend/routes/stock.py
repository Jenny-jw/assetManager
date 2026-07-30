from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.capabilities import require_module
from core.deployment import DeploymentConfig
from dependencies.auth import require_owner, require_tenant_id
from dependencies.db import DbSession
from dependencies.deployment import get_request_deployment
from models.stock import Stock
from schemas.stock import (
    StockCreate,
    StockListResponse,
    StockResponse,
    StockSummaryResponse,
    StockUpdate,
)
from services.stock_queries import (
    coerce_weight_grams_for_edition,
    get_active_stock,
    list_active_stocks,
)
from services.stock_summary_service import build_stock_summary

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
    dependencies=[Depends(require_owner()), Depends(require_module("inventory"))],
)

@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    body: StockCreate,
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
    deployment: DeploymentConfig = Depends(get_request_deployment),
):
    payload = body.model_dump()
    try:
        payload["weight_grams"] = coerce_weight_grams_for_edition(
            payload.get("weight_grams"),
            deployment.edition,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stock = Stock(**payload, tenant_id=tenant_id)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock

@router.get("/", response_model=StockListResponse)
def list_stocks(
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    genre: str | None = None,
    origin: str | None = None,
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|name|genre|origin|quantity|score|price_per_jin|harvest_time)$",
    ),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
):
    rows, total = list_active_stocks(
        db,
        tenant_id=tenant_id,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_direction=sort_direction,
        search=search,
        genre=genre,
        origin=origin,
    )
    return StockListResponse(data=rows, page=page, limit=limit, total=total)

@router.get("/summary", response_model=StockSummaryResponse)
def stock_summary(
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
):
    return build_stock_summary(db, tenant_id=tenant_id)

@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(
    stock_id: str,
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
):
    try:
        stock_uuid = UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stock id") from exc

    stock = get_active_stock(db, stock_uuid, tenant_id=tenant_id)
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock

@router.patch("/{stock_id}", response_model=StockResponse)
def update_stock(
    stock_id: str,
    body: StockUpdate,
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
    deployment: DeploymentConfig = Depends(get_request_deployment),
):
    try:
        stock_uuid = UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stock id") from exc

    stock = get_active_stock(db, stock_uuid, tenant_id=tenant_id)
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

    update_data = body.model_dump(exclude_unset=True)

    for key in ("genre", "origin", "producer", "comment"):
        if key in update_data and update_data[key] == "":
            update_data[key] = None

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if "weight_grams" in update_data:
        try:
            update_data["weight_grams"] = coerce_weight_grams_for_edition(
                update_data["weight_grams"],
                deployment.edition,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for field, value in update_data.items():
        setattr(stock, field, value)

    stock.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(stock)
    return stock

@router.delete("/{stock_id}")
def delete_stock(
    stock_id: str,
    db: DbSession,
    tenant_id: UUID = Depends(require_tenant_id),
):
    try:
        stock_uuid = UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stock id") from exc

    stock = get_active_stock(db, stock_uuid, tenant_id=tenant_id)
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

    now = datetime.now(timezone.utc)
    stock.deleted_at = now
    stock.updated_at = now
    db.commit()
    return {"message": "Stock deleted"}
