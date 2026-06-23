from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core.config import (
    JWT_COOKIE_MAX_AGE_SECONDS,
    JWT_COOKIE_SAMESITE,
    JWT_COOKIE_SECURE,
)
from core.security import create_token, hash_password, verify_password
from dependencies.db import DbSession
from models.product.user import User
from schemas.product.user import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

OWNER_ROLE = "owner"
_SIGNUP_CLOSED_DETAIL = "Signup is disabled after the owner account is created"

def _user_count(db: DbSession) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: DbSession):
    if _user_count(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_SIGNUP_CLOSED_DETAIL,
        )

    owner = User(
        username=body.username,
        name=body.name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=OWNER_ROLE,
        is_active=True,
    )
    db.add(owner)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        ) from None
    db.refresh(owner)
    return owner

@router.post("/login")
def login(body: UserLogin, response: Response, db: DbSession):
    db_user = db.scalar(select(User).where(User.username == body.username))

    if (
        db_user is None
        or not db_user.is_active
        or not verify_password(body.password, db_user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_token({"sub": str(db_user.id), "role": db_user.role})
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
