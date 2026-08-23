from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.deployment import Edition

Score = Annotated[int, Field(ge=0, le=100)]
HarvestDate = Annotated[int, Field(ge=20100101, le=22001231)]
QuantityRange = Annotated[int, Field(ge=0)]
PricePerJin = Annotated[int, Field(ge=0, description="Price per 斤 (600g)")]

class StockBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    genre: str | None = Field(None, max_length=50)
    origin: str | None = Field(None, max_length=100)
    producer: str | None = Field(None, max_length=200)
    roast_level: Score | None = None
    harvest_time: HarvestDate | None = None
    weight_grams: Annotated[int, Field(gt=0)] | None = None
    quantity: QuantityRange = 0
    score: Score | None = None
    price_per_jin: PricePerJin | None = None
    cost_per_jin: PricePerJin | None = None
    comment: str | None = None

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    genre: str | None = Field(None, max_length=50)
    origin: str | None = Field(None, max_length=100)
    producer: str | None = Field(None, max_length=200)
    roast_level: Score | None = None
    harvest_time: HarvestDate | None = None
    weight_grams: Annotated[int, Field(gt=0)] | None = None
    quantity: QuantityRange | None = None
    score: Score | None = None
    price_per_jin: PricePerJin | None = None
    cost_per_jin: PricePerJin | None = None
    comment: str | None = None

class StockResponse(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, value: object) -> str:
        return str(value)

class StockListResponse(BaseModel):
    data: list[StockResponse]
    page: int
    limit: int
    total: int

class StockSummaryResponse(BaseModel):
    total_assets: int
    total_packages: int
    total_weight_grams: int
    total_value: int
    by_origin: dict[str, int]
    by_genre: dict[str, int]

def validate_weight_grams_for_edition(
    weight_grams: int | None,
    edition: Edition,
) -> int | None:
    if weight_grams is None:
        return None
    if edition is Edition.personal and weight_grams not in (75, 150):
        raise ValueError("personal edition allows weight_grams 75 or 150 only")
    return weight_grams