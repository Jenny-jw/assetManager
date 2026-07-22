from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from core.config import (
    JWT_COOKIE_MAX_AGE_SECONDS,
    JWT_COOKIE_SAMESITE,
    JWT_COOKIE_SECURE,
)
from core.security import create_token, hash_password, verify_password
from dependencies.db import DbSession
from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse
from services.tenant_onboarding import (
    assert_tenant_access,
    build_trial_tenant,
    get_tenant_by_slug,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

OWNER_ROLE = "owner"

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: UserCreate, db: DbSession):
    if get_tenant_by_slug(db, body.slug) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug already registered",
        )

    tenant = build_trial_tenant(slug=body.slug, edition=body.edition)
    db.add(tenant)
    db.flush()
    owner = User(
        tenant_id=tenant.id,
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
            detail="Username, email, or tenant slug already registered",
        ) from None
    db.refresh(owner)
    return owner

@router.post("/login")
def login(body: UserLogin, response: Response, db: DbSession):
    tenant = get_tenant_by_slug(db, body.slug)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    assert_tenant_access(tenant)

    db_user = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.username == body.username,
        )
    )
    if (
        db_user is None
        or not db_user.is_active
        or not verify_password(body.password, db_user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_token(
        {
            "sub": str(db_user.id),
            "role": db_user.role,
            "tenant_id": str(tenant.id),
        }
    )
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
