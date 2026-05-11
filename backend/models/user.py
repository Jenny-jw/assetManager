# Define the User structure in database
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    guest = "guest"
    
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.user
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    
class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: str
    created_at: datetime = Field(default_factory=utcnow)

class UserResponse(UserBase):
    id: str
    created_at: datetime