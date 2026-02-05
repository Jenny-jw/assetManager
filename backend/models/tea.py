from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

print(utcnow())

class Tea(BaseModel):
    name: str | None = None
    origin: str = Field(..., json_schema_extra={"example": "Alishan"})
    harvestTime: int | None = Field(None, json_schema_extra={"example": 202506})
    price: int | None = Field(None, json_schema_extra={"example": 300})
    created_at: datetime = Field(default_factory=utcnow)
    
tea = Tea(origin="Sun Moon Lake", harvestTime=202412, price=1000)
print(tea.model_dump()) 