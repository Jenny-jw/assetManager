# Used for API requests and responses
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional, Annotated

def utcnow():
    return datetime.now(timezone.utc)

Score = Annotated[int, Field(ge=0, le=100)]
weightRange = Annotated[int, Field(ge=0)]
quantityRange = Annotated[int, Field(ge=0)]

class ProducerInfo(BaseModel):
    name: str
    factory: Optional[str] = None
    location: Optional[str] = None

class TeaBase(BaseModel):
    name: str = Field(..., example="High mountain oolong tea")
    origin: Optional[str] = Field(None, example="Alishan")
    genre: Optional[str] = Field(None, example="Oolong")
    roast_level: Optional[Score] = Field(None, example=50)
    harvest_time: Optional[int] = Field(None, example=202506)  # YYYYMM
    weight: Optional[weightRange] = Field(None, example=600)   # grams
    quantity: Optional[quantityRange] = Field(None, example=3)
    score: Optional[Score] = Field(None, example=85)
    comment: Optional[str] = Field(None, example="Fruity aroma with a hint of floral notes")
    producer: Optional[ProducerInfo] = None
    owner_id: Optional[str] = None  # reference to user (UUID or str)

class TeaCreate(TeaBase):
    created_at: datetime = Field(default_factory=utcnow)

class TeaUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    genre: Optional[str] = None
    roast_level: Optional[Score] = None
    harvest_time: Optional[int] = None
    weight: Optional[weightRange] = None
    quantity: Optional[quantityRange] = None
    score: Optional[Score] = None
    comment: Optional[str] = None
    producer: Optional[ProducerInfo] = None
    owner_id: Optional[str] = None
# 不要讓 client 設 updated_at；server 在更新時寫入
# updated_at: datetime = Field(default_factory=utcnow)

class TeaResponsePublic(TeaBase):
    id: str
    created_at: datetime

class TeaResponseInternal(TeaResponsePublic):
    owner_id: Optional[str]
    updated_at: Optional[datetime]