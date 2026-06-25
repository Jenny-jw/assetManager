from routes.product.auth import router as auth_router
from routes.product.deployment import router as deployment_router
from routes.product.security import router as security_router
from routes.product.stock import router as stock_router

__all__ = ["auth_router", "deployment_router", "security_router", "stock_router"]
