import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

JWT_COOKIE_SECURE = _as_bool(os.getenv("JWT_COOKIE_SECURE"), True)
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "lax")
JWT_COOKIE_MAX_AGE_SECONDS = int(os.getenv("JWT_COOKIE_MAX_AGE_SECONDS", "3600"))