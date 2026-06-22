from __future__ import annotations

from fastapi import FastAPI

from core.deployment import DeploymentConfig
from core.security import router as security_router
from routes.auth import router as auth_router
from routes.health import router as health_router
from routes.orders import router as orders_router
from routes.tea import router as tea_router

def register_routes(app: FastAPI, deployment: DeploymentConfig) -> None:
    app.include_router(health_router)
    if deployment.modules.inventory:
        app.include_router(tea_router, prefix="/api")
    if deployment.modules.orders:
        app.include_router(orders_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(security_router, prefix="/api")

def route_paths(app: FastAPI) -> set[str]:
    paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
    return paths
