# Used for API requests and responses
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional, Annotated

from core.harvest_date import HarvestYyyymmdd

Score = Annotated[int, Field(ge=0, le=100)]
PackageWeightGrams = Literal[75, 150]
quantityRange = Annotated[int, Field(ge=1)]
pricePerJin = Annotated[int, Field(ge=0, description="Price per 斤 (600g)")]

class TeaBase(BaseModel):
    name: str = Field(..., example="High mountain oolong tea")
    origin: Optional[str] = Field(None, example="Alishan")
    genre: str = Field(..., example="Oolong")
    roast_level: Optional[Score] = Field(None, example=50)
    harvest_time: Optional[HarvestYyyymmdd] = Field(None, example=20260517)
    weight: Optional[PackageWeightGrams] = Field(
        None, description="Grams per package (75 or 150 only)", example=150
    )
    quantity: Optional[quantityRange] = Field(
        None, description="Number of packages in stock (at least 1)", example=3
    )
    score: Optional[Score] = Field(None, example=85)
    price: Optional[pricePerJin] = Field(
        None, description="Price per 斤 (600g)", example=1200
    )
    comment: Optional[str] = Field(None, example="Fruity aroma with a hint of floral notes")
    producer: Optional[str] = None

class TeaCreate(TeaBase):
    weight: PackageWeightGrams
    quantity: quantityRange

class TeaUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    genre: Optional[str] = None
    roast_level: Optional[Score] = None
    harvest_time: Optional[HarvestYyyymmdd] = None
    weight: Optional[PackageWeightGrams] = None
    quantity: Optional[quantityRange] = None
    score: Optional[Score] = None
    price: Optional[pricePerJin] = None
    comment: Optional[str] = None
    producer: Optional[str] = None
# owner_id、created_at、updated_at 由伺服器寫入，不在這個請求模型裡

class TeaResponsePublic(TeaBase):
    id: str
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class TeaResponseList(BaseModel):
    data: list[TeaResponsePublic]
    page: int
    limit: int
    total: int
    errors: list[dict] = []

class TeaSummaryResponse(BaseModel):
    total_assets: int
    total_packages: int
    total_weight_grams: int
    total_value: int
    by_origin: dict[str, int]
    by_genre: dict[str, int]