from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(pwd_input, hashed):
    return pwd_context.verify(pwd_input, hashed)

def create_token(data: dict):
    payload = data.copy()
    expiredAt = datetime.now(timezone.utc) + timedelta(hours=1)
    payload.update({"exp": expiredAt})

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)