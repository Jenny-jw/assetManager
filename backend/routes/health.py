from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from core.db import ping_postgres

router = APIRouter(tags=["Health"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ready")
def ready():
    try:
        ping_postgres()
        return {"status": "ready"}
    except (SQLAlchemyError, RuntimeError):
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "database unreachable"},
        )
