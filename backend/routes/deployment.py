from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.dashboard_widgets import effective_dashboard_layout
from core.deployment import DeploymentConfig, deployment_from_tenant
from core.tenant import get_request_tenant_id
from dependencies.auth import get_current_user
from dependencies.db import DbSession
from models.tenant import Tenant
from schemas.deployment import DeploymentResponse

router = APIRouter(prefix="/deployment", tags=["Deployment"])

def get_current_tenant_deployment(
    request: Request,
    db: DbSession,
    _current_user: dict = Depends(get_current_user),
) -> DeploymentConfig:
    tenant_id = get_request_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return deployment_from_tenant(tenant)

@router.get("", response_model=DeploymentResponse)
def get_deployment_config(
    deployment: DeploymentConfig = Depends(get_current_tenant_deployment),
):
    return {
        "edition": deployment.edition,
        "locale": deployment.locale,
        "modules": deployment.modules,
        "dashboard_layout": effective_dashboard_layout(deployment),
    }
