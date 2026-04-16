# Used for API requests and responses
from pydantic import BaseModel, Field, EmailStr
from models.user import UserRole
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class UserBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Your name"})
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    role: UserRole
    created_at: datetime = Field(default_factory=utcnow)
    is_active: bool