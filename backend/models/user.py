# Define the User structure in database
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    
class UserInDB(BaseModel):
    id: str
    name: str
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.user
    created_at: datetime = Field(default_factory=utcnow)
    is_active: bool = False