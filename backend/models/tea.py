# Stored tea document. id is the hex string of Mongo _id, assigned by the database.
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

def utcnow():
    return datetime.now(timezone.utc)

PackageWeightGrams = Literal[75, 150]

class TeaInDB(BaseModel):
    id: Optional[str] = None
    name: str
    genre: str
    origin: Optional[str] = None
    producer: Optional[str] = None
    comment: Optional[str] = None
    roast_level: Optional[int] = None
    score: Optional[int] = None
    harvest_time: Optional[int] = None
    price: Optional[int] = None
    weight: PackageWeightGrams
    quantity: int = Field(ge=1)
    owner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: Optional[datetime] = None