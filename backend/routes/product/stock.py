from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.deployment import DeploymentConfig, get_deployment
from dependencies.db import DbSession
from dependencies.product.auth import require_owner
from models.product.stock import Stock
from schemas.product.stock import StockCreate, StockResponse
from services.product.stock_queries import coerce_weight_grams_for_edition, get_active_stock

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
