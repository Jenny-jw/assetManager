from __future__ import annotations

from fastapi import APIRouter, Depends

from dependencies.auth import get_current_user
from schemas.user import UserResponse

router = APIRouter(prefix="/security", tags=["Security"])

@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user