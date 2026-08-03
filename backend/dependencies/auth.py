from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
import jwt
from sqlalchemy import select

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from core.tenant import (
    bind_request_tenant,
    clear_current_tenant_id,
    get_request_tenant_id,
)
from dependencies.db import DbSession
from models.tenant import Tenant
from models.user import User
from services.tenant_onboarding import assert_tenant_access

OWNER_ROLE = "owner"

def _auth_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }

def _decode_token_payload(request: Request) -> dict[str, Any]:
    token = request.cookies.get("token")
    if not token:
        raise _auth_error("Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise _auth_error("Invalid or expired token") from exc

    if not isinstance(payload, dict):
        raise _auth_error("Invalid token payload")
    return payload

def _parse_uuid_claim(value: object) -> UUID:
    if value is None:
        raise _auth_error("Invalid token payload")
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise _auth_error("Invalid token payload") from exc

def get_current_user(request: Request, db: DbSession) -> dict[str, Any]:
    clear_current_tenant_id()
    bind_request_tenant(request, None)
    payload = _decode_token_payload(request)
    user_id = _parse_uuid_claim(payload.get("sub"))
    tenant_id = _parse_uuid_claim(payload.get("tenant_id"))

    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise _auth_error("Invalid token payload")
    assert_tenant_access(tenant)
    bind_request_tenant(request, tenant_id)

    if not user.is_active:
        clear_current_tenant_id()
        bind_request_tenant(request, None)
        raise _auth_error("Not authenticated")
    return user_to_dict(user)

def require_owner():
    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("role") != OWNER_ROLE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _checker

def require_tenant_id(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UUID:
    tenant_id = get_request_tenant_id(request)
    if tenant_id is not None:
        return tenant_id
    raw = current_user.get("tenant_id")
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_required",
        )
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant_required",
        ) from exc
