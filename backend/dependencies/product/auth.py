from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from dependencies.db import DbSession
from models.product.user import User

OWNER_ROLE = "owner"

def _auth_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }

def _token_sub(request: Request) -> str:
    token = request.cookies.get("token")
    if not token:
        raise _auth_error("Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise _auth_error("Invalid or expired token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise _auth_error("Invalid token payload")

    try:
        UUID(str(user_id))
    except ValueError as exc:
        raise _auth_error("Invalid token payload") from exc

    return str(user_id)

def get_current_user(request: Request, db: DbSession) -> dict[str, Any]:
    user = db.get(User, UUID(_token_sub(request)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise _auth_error("Not authenticated")
    return user_to_dict(user)

def require_owner():
    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("role") != OWNER_ROLE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _checker
