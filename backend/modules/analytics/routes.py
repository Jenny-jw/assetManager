from fastapi import APIRouter, Depends

from core.capabilities import Capability, require_capability, require_module
from dependencies.auth import require_owner
from dependencies.repositories import get_stock_repository
from repositories.postgres.stock_repository import StockRepository
from schemas.profit import ProfitSummaryResponse
from services.profit_analytics_service import build_profit_summary

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[
        Depends(require_module("profit_analytics")),
        Depends(require_owner()),
        Depends(require_capability(Capability.view_profit)),
    ],
)

@router.get("/profit", response_model=ProfitSummaryResponse)
def profit_summary(
    repo: StockRepository = Depends(get_stock_repository),
):
    return build_profit_summary(repo)