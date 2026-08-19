from pydantic import BaseModel, ConfigDict, field_validator

class ProfitLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_id: str
    name: str
    quantity: int
    retail_value: int
    cost_value: int
    profit: int | None
    priced: bool
    costed: bool

    @field_validator("stock_id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        return str(value)

class ProfitSummaryResponse(BaseModel):
    total_retail_value: int
    total_cost_value: int
    unrealized_profit: int
    priced_assets: int
    costed_assets: int
    complete_assets: int
    uncosted_assets: int
    by_origin: dict[str, int]
    by_genre: dict[str, int]
    lines: list[ProfitLineResponse]