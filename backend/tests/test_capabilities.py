from pathlib import Path

import pytest

from core.capabilities import (
    Capability,
    capability_denial_detail,
    has_capability,
    resolve_capabilities,
)
from core.deployment import load_deployment_config, reset_deployment_cache

_REPO_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(autouse=True)
def clear_deployment_cache():
    reset_deployment_cache()
    yield
    reset_deployment_cache()

def _preset_path(name: str) -> Path:
    return _REPO_ROOT / "deploy" / "presets" / name

def _owner_user() -> dict:
    return {"id": "1", "role": "owner"}

def test_personal_owner_gets_inventory_not_orders():
    deployment = load_deployment_config(_preset_path("personal.yaml"))
    caps = resolve_capabilities(_owner_user(), deployment)
    assert Capability.manage_inventory in caps
    assert Capability.view_pricing in caps
    assert Capability.approve_orders not in caps
    assert Capability.view_profit not in caps

def test_professional_owner_gets_orders_and_profit():
    deployment = load_deployment_config(_preset_path("professional.yaml"))
    caps = resolve_capabilities(_owner_user(), deployment)
    assert Capability.approve_orders in caps
    assert Capability.view_profit in caps

def test_role_not_enabled_returns_no_capabilities():
    deployment = load_deployment_config(_preset_path("personal.yaml"))
    caps = resolve_capabilities({"id": "2", "role": "customer"}, deployment)
    assert caps == frozenset()
    detail = capability_denial_detail(
        {"id": "2", "role": "customer"},
        Capability.manage_inventory,
        deployment,
    )
    assert detail == "role_not_enabled"

def test_module_disabled_detail_for_personal_orders():
    deployment = load_deployment_config(_preset_path("personal.yaml"))
    detail = capability_denial_detail(
        _owner_user(),
        Capability.approve_orders,
        deployment,
    )
    assert detail == "module_disabled"

def test_has_capability_helper():
    deployment = load_deployment_config(_preset_path("professional.yaml"))
    assert has_capability(_owner_user(), Capability.view_profit, deployment) is True
    assert has_capability(_owner_user(), "manage_inventory", deployment) is True

def test_v1_roles_not_used_in_product_capabilities():
    deployment = load_deployment_config(_preset_path("professional.yaml"))
    for legacy_role in ("admin", "user", "guest"):
        caps = resolve_capabilities({"id": "x", "role": legacy_role}, deployment)
        assert caps == frozenset()
