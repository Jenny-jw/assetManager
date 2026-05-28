# Define the Tea structure in database
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class TeaInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid1()))
    name: str
    origin: Optional[str] = None
    genre: Optional[str] = None
    roast_level: Optional[int] = None
    harvest_time: Optional[int] = None
    roast_time: Optional[int] = None
    weight: Optional[int] = None
    quantity: Optional[int] = None
    score: Optional[int] = None
    comment: Optional[str] = None
    producer: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

# cost: int = Field(..., json_schema_extra={"example": 300})
# price: int | None = Field(None, json_schema_extra={"example": 300}) 
# price per unit size in UI
# roast_level: 0~100%
# Tea owner
# Producer / factory, personal taste & score