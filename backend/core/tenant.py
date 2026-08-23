from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

from starlette.requests import Request

_current_tenant_id: ContextVar[UUID | None] = ContextVar(
    "current_tenant_id",
    default=None,
)

def get_current_tenant_id() -> UUID | None:
    return _current_tenant_id.get()

def set_current_tenant_id(tenant_id: UUID | None) -> None:
    _current_tenant_id.set(tenant_id)

def clear_current_tenant_id() -> None:
    _current_tenant_id.set(None)

def bind_request_tenant(request: Request, tenant_id: UUID | None) -> None:
    """Attach tenant to the request (reliable for sync FastAPI handlers)."""
    request.state.tenant_id = tenant_id
    set_current_tenant_id(tenant_id)

def get_request_tenant_id(request: Request) -> UUID | None:
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is not None:
        return tenant_id
    return get_current_tenant_id()
