# from __future__ import annotations
import core.env  # noqa: F401 — repo-root .env (product branch only)
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.db import ping_postgres
from core.deployment import DeploymentConfig, get_deployment
from core.errors import register_exception_handlers
from core.logging import RequestLoggingMiddleware, configure_logging
from core.router_registry import register_routes

configure_logging()

origins = [
    "http://localhost:5173",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    ping_postgres()
    yield

def create_app(deployment: DeploymentConfig | None = None) -> FastAPI:
    active_deployment = deployment or get_deployment()
    app = FastAPI(title="Asset Manager API", version="0.1.0", lifespan=lifespan)
    if deployment is not None:
        app.dependency_overrides[get_deployment] = lambda: active_deployment
    register_routes(app)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    return app

get_deployment()
app = create_app()