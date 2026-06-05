# Used for API requests and responses
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Literal, Optional, Annotated

def utcnow():
    return datetime.now(timezone.utc)

Score = Annotated[int, Field(ge=0, le=100)]
PackageWeightGrams = Literal[75, 150]
quantityRange = Annotated[int, Field(ge=0)]
harvestDate = Annotated[int, Field(ge=20100101, le=22001231)]
pricePerJin = Annotated[int, Field(ge=0, description="Price per 斤 (600g)")]

class TeaBase(BaseModel):
    name: str = Field(..., example="High mountain oolong tea")
    origin: Optional[str] = Field(None, example="Alishan")
    genre: str = Field(..., example="Oolong")
    roast_level: Optional[Score] = Field(None, example=50)
    harvest_time: Optional[harvestDate] = Field(None, example=20260517)
    weight: Optional[PackageWeightGrams] = Field(
        None, description="Grams per package (75 or 150 only)", example=150
    )
    quantity: Optional[quantityRange] = Field(
        None, description="Number of packages in stock", example=3
    )
    score: Optional[Score] = Field(None, example=85)
    price: Optional[pricePerJin] = Field(
        None, description="Price per 斤 (600g)", example=1200
    )
    comment: Optional[str] = Field(None, example="Fruity aroma with a hint of floral notes")
    producer: Optional[str] = None
    owner_id: Optional[str] = None # reference to user (UUID or str)

class TeaCreate(TeaBase):
    created_at: datetime = Field(default_factory=utcnow)

class TeaUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    genre: Optional[str] = None
    roast_level: Optional[Score] = None
    harvest_time: Optional[harvestDate] = None
    weight: Optional[PackageWeightGrams] = None
    quantity: Optional[quantityRange] = None
    score: Optional[Score] = None
    price: Optional[pricePerJin] = None
    comment: Optional[str] = None
    producer: Optional[str] = None
    owner_id: Optional[str] = None
# 不要讓 client 設 updated_at；server 在更新時寫入
# updated_at: datetime = Field(default_factory=utcnow)

class TeaResponsePublic(TeaBase):
    id: str
    created_at: datetime

class TeaResponseList(BaseModel):
    data: list[TeaResponsePublic]
    page: int
    limit: int
    total: int
    errors: list[dict] = []

class TeaResponseInternal(TeaResponsePublic):
    owner_id: Optional[str]
    updated_at: Optional[datetime]