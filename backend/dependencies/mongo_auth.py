"""Mongo JWT auth for v1 orders routes — removed in Phase 2 with orders Mongo."""
from enum import Enum
from typing import Any

from bson import ObjectId
from fastapi import Depends, Request, status
import jwt

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from core.errors import ApiError, ErrorCode, api_error
from core.mongo_legacy import db

class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    guest = "guest"

def _auth_error(code: ErrorCode) -> ApiError:
    return api_error(status.HTTP_401_UNAUTHORIZED, code)

def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("token")
    if not token:
        raise _auth_error(ErrorCode.not_authenticated)

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise _auth_error(ErrorCode.invalid_token) from exc

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        raise _auth_error(ErrorCode.invalid_token_payload)

    current_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.user_not_found)

    current_user["id"] = str(current_user["_id"])
    return current_user

def require_role(*roles: UserRole):
    allowed_values = {role.value if isinstance(role, UserRole) else str(role) for role in roles}

    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        role = current_user.get("role")
        role_value = role.value if isinstance(role, UserRole) else str(role)
        if role_value not in allowed_values:
            raise api_error(status.HTTP_403_FORBIDDEN, ErrorCode.forbidden)
        return current_user

    return _checker