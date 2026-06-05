from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from core.db import client

router = APIRouter(tags=["Health"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ready")
def ready():
    try:
        client.admin.command("ping")
        return {"status": "ready"}
    except PyMongoError:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "database unreachable"},
        )