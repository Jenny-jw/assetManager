from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import Depends, status

from core.deployment import DeploymentConfig, DeploymentModules
from core.errors import ErrorCode, api_error
from dependencies.auth import get_current_user
from dependencies.deployment import get_request_deployment

class Capability(str, Enum):
    manage_inventory = "manage_inventory"
    view_pricing = "view_pricing"
    view_profit = "view_profit"
    approve_orders = "approve_orders"
    view_catalog = "view_catalog"

CAPABILITY_MODULE: dict[Capability, str] = {
    Capability.manage_inventory: "inventory",
    Capability.view_pricing: "pricing_visibility",
    Capability.view_profit: "profit_analytics",
    Capability.approve_orders: "orders",
    Capability.view_catalog: "inventory",
}

ROLE_CAPABILITIES: dict[str, frozenset[Capability]] = {
    "owner": frozenset(
        {
            Capability.manage_inventory,
            Capability.view_pricing,
            Capability.view_profit,
            Capability.approve_orders,
            Capability.view_catalog,
        }
    ),
}

def _role_value(role: Any) -> str:
    if role is None:
        return ""
    return role.value if hasattr(role, "value") else str(role)

def _effective_role(role: str, deployment: DeploymentConfig) -> str | None:
    if role not in deployment.roles_enabled:
        return None
    if role not in ROLE_CAPABILITIES:
        return None
    return role

def _module_flag(modules: DeploymentModules, module_key: str) -> bool:
    return bool(getattr(modules, module_key, False))

def _capability_enabled(capability: Capability, modules: DeploymentModules) -> bool:
    module_key = CAPABILITY_MODULE[capability]
    return _module_flag(modules, module_key)

def resolve_capabilities(
    user: dict[str, Any],
    deployment: DeploymentConfig,
) -> frozenset[Capability]:
    role = _role_value(user.get("role"))
    effective_role = _effective_role(role, deployment)
    if effective_role is None:
        return frozenset()

    base_caps = ROLE_CAPABILITIES[effective_role]
    return frozenset(
        cap for cap in base_caps if _capability_enabled(cap, deployment.modules)
    )

def granted_capabilities(
    user: dict[str, Any],
    deployment: DeploymentConfig,
) -> list[str]:
    return sorted(cap.value for cap in resolve_capabilities(user, deployment))

def has_capability(
    user: dict[str, Any],
    capability: Capability | str,
    deployment: DeploymentConfig,
) -> bool:
    cap = Capability(capability) if isinstance(capability, str) else capability
    return cap in resolve_capabilities(user, deployment)

def capability_denial_detail(
    user: dict[str, Any],
    capability: Capability,
    deployment: DeploymentConfig,
) -> ErrorCode:
    role = _role_value(user.get("role"))
    effective_role = _effective_role(role, deployment)
    if effective_role is None:
        return ErrorCode.role_not_enabled

    if capability not in ROLE_CAPABILITIES[effective_role]:
        return ErrorCode.capability_disabled

    if not _capability_enabled(capability, deployment.modules):
        return ErrorCode.module_disabled

    return ErrorCode.capability_disabled

def require_module(module_key: str):
    def _checker(
        deployment: DeploymentConfig = Depends(get_request_deployment),
    ) -> DeploymentConfig:
        if not _module_flag(deployment.modules, module_key):
            raise api_error(status.HTTP_403_FORBIDDEN, ErrorCode.module_disabled)
        return deployment

    return _checker

def require_capability(capability: Capability | str):
    cap = Capability(capability) if isinstance(capability, str) else capability

    def _checker(
        current_user: dict[str, Any] = Depends(get_current_user),
        deployment: DeploymentConfig = Depends(get_request_deployment),
    ) -> dict[str, Any]:
        if has_capability(current_user, cap, deployment):
            return current_user
        raise api_error(
            status.HTTP_403_FORBIDDEN,
            capability_denial_detail(current_user, cap, deployment),
        )

    return _checker
