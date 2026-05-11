from fastapi import APIRouter, Depends, HTTPException
from models.user import UserRole, UserCreate, UserResponse
from backend.core.db import db
from routes.auth import hash_password, get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/user", tags=["User"])

def utcnow():
    return datetime.now(timezone.utc)

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, current_user = Depends(get_current_user)):
    # Only admin can assign admin role
    if user.role == UserRole.admin and (current_user.role != UserRole.admin or current_user is None):
        raise HTTPException(status_code=403, detail="Only admins can create admin users")
    
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashedpw = hash_password(user.password)
    user_doc = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hashedpw,
        "role": user.role.value,
        "created_at": utcnow(),
        "is_active": True
    }
    
    res = db.users.insert_one(user_doc)
    user_response = UserResponse(id=str(res.inserted_id), name=user_doc["name"], email=user_doc["email"], role=user_doc["role"], is_active=user_doc["is_active"], created_at=user_doc["created_at"])
    return user_response