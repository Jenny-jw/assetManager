from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from core.capabilities import granted_capabilities
from core.dashboard_widgets import effective_dashboard_layout
from core.deployment import DeploymentConfig
from dependencies.auth import get_current_user
from dependencies.deployment import get_current_tenant_deployment
from schemas.deployment import DeploymentResponse

router = APIRouter(prefix="/deployment", tags=["Deployment"])

@router.get("", response_model=DeploymentResponse)
def get_deployment_config(
    deployment: DeploymentConfig = Depends(get_current_tenant_deployment),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    return {
        "edition": deployment.edition,
        "locale": deployment.locale,
        "modules": deployment.modules,
        "dashboard_layout": effective_dashboard_layout(deployment),
        "capabilities": granted_capabilities(current_user, deployment),
    }
