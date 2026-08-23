from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, Request, status
import jwt

from core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from core.db import get_session_factory
from core.deployment import DeploymentConfig, deployment_from_tenant, get_deployment
from core.errors import ErrorCode, api_error
from core.tenant import get_request_tenant_id
from dependencies.auth import get_current_user
from dependencies.db import DbSession
from models.tenant import Tenant

def get_current_tenant_deployment(
    request: Request,
    db: DbSession,
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> DeploymentConfig:
    """Strict tenant-backed config for authenticated PG users (e.g. GET /deployment)."""
    tenant_id = get_request_tenant_id(request)
    if tenant_id is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.tenant_not_found)
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise api_error(status.HTTP_404_NOT_FOUND, ErrorCode.tenant_not_found)
    return deployment_from_tenant(tenant)

def _tenant_id_from_token(request: Request) -> UUID | None:
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if not isinstance(payload, dict):
        return None
    raw = payload.get("tenant_id")
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None

def get_request_deployment(
    request: Request,
    process_deployment: DeploymentConfig = Depends(get_deployment),
) -> DeploymentConfig:
    """Resolve modules for the current request.

    Prefer the JWT tenant row when present (SaaS path). Fall back to process-global
    YAML deployment so legacy Mongo order routes keep working until Phase 2.
    """
    tenant_id = get_request_tenant_id(request) or _tenant_id_from_token(request)
    if tenant_id is None:
        return process_deployment

    db = get_session_factory()()
    try:
        tenant = db.get(Tenant, tenant_id)
        if tenant is None:
            return process_deployment
        return deployment_from_tenant(tenant)
    finally:
        db.close()
