# 處理密碼雜湊與 Token 生成
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, Depends
from schemas.user import UserResponse
from middleware.auth import get_current_user

router = APIRouter(prefix="/security", tags=["Security"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(pwd_input, hashed):
    return pwd_context.verify(pwd_input, hashed)

def create_token(data: dict):
    payload = data.copy()
    expiredAt = datetime.now(timezone.utc) + timedelta(hours=1)
    payload.update({"exp": expiredAt})
   
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/me", response_model=UserResponse)
def me(current_user = Depends(get_current_user)):
    return current_user