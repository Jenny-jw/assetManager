from __future__ import annotations

from fastapi import APIRouter, Depends

from core.dashboard_widgets import effective_dashboard_layout
from core.deployment import DeploymentConfig, get_deployment
from schemas.product.deployment import DeploymentResponse

router = APIRouter(prefix="/deployment", tags=["Deployment"])

@router.get("", response_model=DeploymentResponse)
def get_deployment_config(
    deployment: DeploymentConfig = Depends(get_deployment),
):
    return {
        "edition": deployment.edition,
        "locale": deployment.locale,
        "modules": deployment.modules,
        "dashboard_layout": effective_dashboard_layout(deployment),
    }
