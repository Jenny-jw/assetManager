from __future__ import annotations

from core.tea_pricing import line_total_value, line_unrealized_profit
from models.stock import Stock
from repositories.postgres.stock_repository import StockRepository
from schemas.profit import ProfitLineResponse, ProfitSummaryResponse

def _line_from_stock(stock: Stock) -> ProfitLineResponse:
    priced = stock.price_per_jin is not None and stock.weight_grams is not None
    costed = stock.cost_per_jin is not None and stock.weight_grams is not None
    retail_value = line_total_value(
        stock.price_per_jin,
        stock.weight_grams,
        stock.quantity,
    )
    cost_value = line_total_value(
        stock.cost_per_jin,
        stock.weight_grams,
        stock.quantity,
    )
    return ProfitLineResponse(
        stock_id=str(stock.id),
        name=stock.name,
        quantity=stock.quantity,
        retail_value=retail_value,
        cost_value=cost_value,
        profit=line_unrealized_profit(
            stock.price_per_jin,
            stock.cost_per_jin,
            stock.weight_grams,
            stock.quantity,
        ),
        priced=priced,
        costed=costed,
    )

def build_profit_summary(repo: StockRepository) -> ProfitSummaryResponse:
    total_retail_value = 0
    total_cost_value = 0
    unrealized_profit = 0
    priced_assets = 0
    costed_assets = 0
    complete_assets = 0
    uncosted_assets = 0
    by_origin: dict[str, int] = {}
    by_genre: dict[str, int] = {}
    lines: list[ProfitLineResponse] = []

    for stock in repo.list_all_active():
        line = _line_from_stock(stock)
        lines.append(line)
        if line.priced:
            priced_assets += 1
            total_retail_value += line.retail_value
        if line.costed:
            costed_assets += 1
            total_cost_value += line.cost_value
        else:
            uncosted_assets += 1
        if line.profit is not None:
            complete_assets += 1
            unrealized_profit += line.profit
            origin = stock.origin or "Unknown"
            genre = stock.genre or "Unknown"
            by_origin[origin] = by_origin.get(origin, 0) + line.profit
            by_genre[genre] = by_genre.get(genre, 0) + line.profit

    return ProfitSummaryResponse(
        total_retail_value=total_retail_value,
        total_cost_value=total_cost_value,
        unrealized_profit=unrealized_profit,
        priced_assets=priced_assets,
        costed_assets=costed_assets,
        complete_assets=complete_assets,
        uncosted_assets=uncosted_assets,
        by_origin=by_origin,
        by_genre=by_genre,
        lines=lines,
    )