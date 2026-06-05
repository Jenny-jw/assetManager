# /login、/signup、/logout
from fastapi import APIRouter, HTTPException, Response
from models.user import UserRole
from schemas.user import UserLogin, UserCreate, UserResponse
from core.db import db
from core.config import (
    JWT_COOKIE_MAX_AGE_SECONDS,
    JWT_COOKIE_SAMESITE,
    JWT_COOKIE_SECURE,
)
from core.security import hash_password, verify_password, create_token
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Auth"])

def utcnow():
    return datetime.now(timezone.utc)

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate):
    # Only admin can assign admin role
    # if user.role == UserRole.admin:
    #     raise HTTPException(status_code=403, detail="Only admins can create admin users")

    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashedpw = hash_password(user.password)
    user_doc = {
        "name": user.name,
        "email": user.email,
        "hashed_password": hashedpw,
        "role": UserRole.user,
        "created_at": utcnow(),
        "is_active": True
    }

    res = db.users.insert_one(user_doc)
    return {
        "id": str(res.inserted_id),
        **user_doc
    }

@router.post("/login")
def login(user: UserLogin, response: Response):
    db_user = db.users.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token({"sub": str(db_user["_id"]), "role": db_user["role"]})
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=JWT_COOKIE_SECURE,
        samesite=JWT_COOKIE_SAMESITE,
        max_age=JWT_COOKIE_MAX_AGE_SECONDS,
    )

    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="token",
        httponly=True,
        secure=JWT_COOKIE_SECURE,
        samesite=JWT_COOKIE_SAMESITE,
    )
    return {"message": "Logout successful"}