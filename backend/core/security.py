# 處理密碼雜湊與 Token 生成
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, HTTPException, Request
from schemas.user import UserResponse
from core.db import db

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
def get_current_user(request: Request):
    token = request.cookies.get("token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    user_id = payload.get("sub")
    current_user = db.users.find_one({"_id": user_id})
    
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")
    
    current_user["id"] = str(current_user["_id"])
    
    return current_user