from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.capabilities import require_module
from core.deployment import DeploymentConfig
from dependencies.auth import require_owner
from dependencies.deployment import get_request_deployment
from dependencies.repositories import get_stock_repository
from repositories.postgres.stock_repository import StockRepository
from schemas.stock import (
    StockCreate,
    StockListResponse,
    StockResponse,
    StockSummaryResponse,
    StockUpdate,
)
from services.stock_queries import coerce_weight_grams_for_edition
from services.stock_summary_service import build_stock_summary

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
    dependencies=[Depends(require_owner()), Depends(require_module("inventory"))],
)

def _parse_stock_id(stock_id: str) -> UUID:
    try:
        return UUID(stock_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stock id",
        ) from exc

@router.post("/", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    body: StockCreate,
    repo: StockRepository = Depends(get_stock_repository),
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

    return repo.create(**payload)

@router.get("/", response_model=StockListResponse)
def list_stocks(
    repo: StockRepository = Depends(get_stock_repository),
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
    rows, total = repo.list_active(
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
    repo: StockRepository = Depends(get_stock_repository),
):
    return build_stock_summary(repo)

@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(
    stock_id: str,
    repo: StockRepository = Depends(get_stock_repository),
):
    stock = repo.get_active(_parse_stock_id(stock_id))
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return stock

@router.patch("/{stock_id}", response_model=StockResponse)
def update_stock(
    stock_id: str,
    body: StockUpdate,
    repo: StockRepository = Depends(get_stock_repository),
    deployment: DeploymentConfig = Depends(get_request_deployment),
):
    stock = repo.get_active(_parse_stock_id(stock_id))
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

    return repo.update(stock, update_data)

@router.delete("/{stock_id}")
def delete_stock(
    stock_id: str,
    repo: StockRepository = Depends(get_stock_repository),
):
    stock = repo.get_active(_parse_stock_id(stock_id))
    if stock is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")

    repo.soft_delete(stock)
    return {"message": "Stock deleted"}