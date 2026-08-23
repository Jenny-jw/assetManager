from __future__ import annotations

from enum import Enum

from core.deployment import DeploymentConfig, DeploymentModules

class DashboardWidget(str, Enum):
    summary = "summary"
    origin = "origin"
    genre = "genre"
    recent_assets = "recent_assets"
    pending_orders = "pending_orders"
    profit = "profit"

ALL_DASHBOARD_WIDGETS = frozenset(widget.value for widget in DashboardWidget)
ORDER_DASHBOARD_WIDGETS = frozenset({DashboardWidget.pending_orders.value})
PROFIT_DASHBOARD_WIDGETS = frozenset({DashboardWidget.profit.value})
PERSONAL_DASHBOARD_WIDGETS = (
    ALL_DASHBOARD_WIDGETS - ORDER_DASHBOARD_WIDGETS - PROFIT_DASHBOARD_WIDGETS
)

_WIDGET_MODULE_KEYS: dict[str, str] = {
    DashboardWidget.summary.value: "dashboard_summary",
    DashboardWidget.origin.value: "dashboard_origin_chart",
    DashboardWidget.genre.value: "dashboard_genre_chart",
    DashboardWidget.recent_assets.value: "dashboard_recent_assets",
    DashboardWidget.pending_orders.value: "orders",
    DashboardWidget.profit.value: "profit_analytics",
}

def widget_module_key(widget_id: str) -> str | None:
    return _WIDGET_MODULE_KEYS.get(widget_id)

def widget_enabled(widget_id: str, modules: DeploymentModules) -> bool:
    module_key = widget_module_key(widget_id)
    if module_key is None:
        return False
    return bool(getattr(modules, module_key, False))

def effective_dashboard_layout(config: DeploymentConfig) -> list[str]:
    return [
        widget_id
        for widget_id in config.dashboard_layout
        if widget_enabled(widget_id, config.modules)
    ]