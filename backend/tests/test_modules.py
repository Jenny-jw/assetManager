from fastapi import FastAPI

from core.router_registry import register_routes
from modules.analytics import router as analytics_router
from modules.inventory import router as inventory_router
from modules.orders import router as orders_router

def test_module_packages_export_domain_routers():
    assert inventory_router.prefix == "/stock"
    assert orders_router.prefix == "/orders"
    assert analytics_router.prefix == "/analytics"

def test_register_routes_includes_all_module_routers():
    app = FastAPI()
    included: list[object] = []
    original = app.include_router

    def capture(router, **kwargs):
        included.append(router)
        return original(router, **kwargs)

    app.include_router = capture  # type: ignore[method-assign]
    register_routes(app)

    assert inventory_router in included
    assert orders_router in included
    assert analytics_router in included
