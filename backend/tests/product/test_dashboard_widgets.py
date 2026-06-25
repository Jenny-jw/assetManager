from pathlib import Path

from core.dashboard_widgets import (
    ORDER_DASHBOARD_WIDGETS,
    PERSONAL_DASHBOARD_WIDGETS,
    effective_dashboard_layout,
    widget_enabled,
    widget_module_key,
)
from core.deployment import DeploymentModules, load_deployment_config, load_personal_preset

_REPO_ROOT = Path(__file__).resolve().parents[3]

def _preset_path(name: str) -> Path:
    return _REPO_ROOT / "deploy" / "presets" / name

def test_widget_module_key_maps_summary_to_dashboard_summary():
    assert widget_module_key("summary") == "dashboard_summary"

def test_widget_module_key_maps_pending_orders_to_orders_module():
    assert widget_module_key("pending_orders") == "orders"

def test_widget_module_key_returns_none_for_unknown():
    assert widget_module_key("unknown_widget") is None

def test_personal_preset_widgets_exclude_order_widgets():
    assert "pending_orders" not in PERSONAL_DASHBOARD_WIDGETS
    assert "pending_orders" in ORDER_DASHBOARD_WIDGETS

def test_personal_effective_layout_excludes_pending_orders():
    config = load_personal_preset()
    layout = effective_dashboard_layout(config)
    assert layout == ["summary", "origin", "genre", "recent_assets"]
    assert "pending_orders" not in layout

def test_professional_effective_layout_includes_pending_orders():
    config = load_deployment_config(_preset_path("professional.yaml"))
    layout = effective_dashboard_layout(config)
    assert "pending_orders" in layout

def test_widget_enabled_respects_modules_orders_flag():
    modules = DeploymentModules(
        inventory=True,
        dashboard_summary=True,
        dashboard_origin_chart=True,
        dashboard_genre_chart=True,
        dashboard_recent_assets=True,
        orders=False,
        order_notifications=False,
        pricing_visibility=True,
        profit_analytics=False,
    )
    assert widget_enabled("summary", modules) is True
    assert widget_enabled("pending_orders", modules) is False