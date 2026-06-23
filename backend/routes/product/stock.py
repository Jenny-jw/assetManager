from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.deployment import DeploymentConfig, get_deployment
from dependencies.db import DbSession
from dependencies.product.auth import require_owner
from models.product.stock import Stock
from schemas.product.stock import StockCreate, StockListResponse, StockResponse, StockUpdate
from services.product.stock_queries import (
    coerce_weight_grams_for_edition,
    get_active_stock,
    list_active_stocks,
)

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
    dependencies=[Depends(require_owner())],
)

@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    body: StockCreate,
    db: DbSession,
    deployment: DeploymentConfig = Depends(get_deployment),
):
    payload = body.model_dump()
    try:
        payload["weight_grams"] = coerce_weight_grams_for_edition(
            payload.get("weight_grams"),
            deployment.edition,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stock = Stock(**payload)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock

@router.get("/", response_model=StockListResponse)
def list_stocks(
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|name|genre|origin|quantity|score|price_per_jin|harvest_time)$",
    ),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
):
    rows, total = list_active_stocks(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )
    return StockListResponse(data=rows, page=page, limit=limit, total=total)

@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: str, db: DbSession):
    try:
        stock_uuid = UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stock id") from exc

    stock = get_active_stock(db, stock_uuid)
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock

@router.patch("/{stock_id}", response_model=StockResponse)
def update_stock(
    stock_id: str,
    body: StockUpdate,
    db: DbSession,
    deployment: DeploymentConfig = Depends(get_deployment),
):
    try:
        stock_uuid = UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stock id") from exc

    stock = get_active_stock(db, stock_uuid)
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
