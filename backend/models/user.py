from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    
class User(BaseModel):
    id: str | None = None
    name: str = Field(..., json_schema_extra={"example": "Guigui"})
    role: UserRole = UserRole.user
    created_at: datetime 