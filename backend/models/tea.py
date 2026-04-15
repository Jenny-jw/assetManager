from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class TeaBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "High mountain oolong tea"})
    origin: str | None = Field(None, json_schema_extra={"example": "Alishan"})
    genre: str | None = Field(None, json_schema_extra={"example": "Oolong"})
    roastLevel: int | None = Field(None, json_schema_extra={"example": 50})
    harvestTime: int | None = Field(None, json_schema_extra={"example": 202506})
    weight: int | None = Field(None, json_schema_extra={"example": 600})
    quantity: int | None = Field(None, json_schema_extra={"example": 3})

class TeaCreate(TeaBase):
    created_at: datetime = Field(default_factory=utcnow)

class TeaUpdate(BaseModel):
    name: str | None = None
    origin: str | None = None
    genre: str | None = None
    roastLevel: int | None = None
    harvestTime: int | None = None
    weight: int | None = None
    quantity: int | None = None
    updated_at: datetime = Field(default_factory=utcnow)

class TeaResponse(TeaBase):
    id: str
    created_at: datetime

# cost: int = Field(..., json_schema_extra={"example": 300})
# price: int | None = Field(None, json_schema_extra={"example": 300}) 
# price per unit size in UI
# roastLevel: 0~100%