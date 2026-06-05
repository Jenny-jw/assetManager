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

class UserInDB(BaseModel):
    id: Optional[str] = None
    name: str
    email: EmailStr
    role: UserRole = UserRole.user
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)