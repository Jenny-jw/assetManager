from __future__ import annotations

from fastapi import FastAPI

from routes import auth_router, deployment_router, security_router, stock_router
from routes.health import router as health_router
from routes.orders import router as orders_router

def register_routes(app: FastAPI) -> None:
    """Register all module routers; enforce modules per request (ADR 005 / P1-5f)."""
    app.include_router(health_router)
    app.include_router(stock_router, prefix="/api")
    app.include_router(orders_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(deployment_router, prefix="/api")
    app.include_router(security_router, prefix="/api")

def route_paths(app: FastAPI) -> set[str]:
    paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            paths.add(path)
    return paths
