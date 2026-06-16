# from __future__ import annotations
import core.env  # noqa: F401 — repo-root .env before other core imports
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.tea import router as tea_router
from routes.orders import router as orders_router
from routes.auth import router as auth_router
from routes.health import router as health_router
from core.security import router as security_router
from fastapi.middleware.cors import CORSMiddleware
from core.db import ping_postgres
from core.deployment import get_deployment
from core.errors import register_exception_handlers
from core.logging import RequestLoggingMiddleware, configure_logging

configure_logging()
get_deployment()

origins = [
    "http://localhost:5173",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    ping_postgres()
    yield

app = FastAPI(title="Asset Manager API", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(tea_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(security_router, prefix="/api")
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
register_exception_handlers(app)