from typing import Any

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from core.db import db
from models.user import UserRole

def _auth_error(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def get_current_user(request: Request) -> dict[str, Any]:
    token = request.cookies.get("token")
    if not token:
        raise _auth_error("Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise _auth_error("Invalid or expired token") from exc

    user_id = payload.get("sub")
    if not user_id or not ObjectId.is_valid(user_id):
        raise _auth_error("Invalid token payload")

    current_user = db.users.find_one({"_id": ObjectId(user_id)})
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    current_user["id"] = str(current_user["_id"])
    return current_user

def require_role(*roles: UserRole):
    allowed_values = {role.value if isinstance(role, UserRole) else str(role) for role in roles}

    def _checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        role = current_user.get("role")
        role_value = role.value if isinstance(role, UserRole) else str(role)
        if role_value not in allowed_values:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return _checker