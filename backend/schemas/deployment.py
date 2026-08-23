from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from core.capabilities import Capability
from core.deployment import Edition, Locale

class DeploymentModulesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    inventory: bool
    dashboard_summary: bool
    dashboard_origin_chart: bool
    dashboard_genre_chart: bool
    dashboard_recent_assets: bool
    orders: bool
    order_notifications: bool
    pricing_visibility: bool
    profit_analytics: bool

class DeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    edition: Edition
    locale: Locale
    modules: DeploymentModulesResponse
    dashboard_layout: list[str] = Field(min_length=1)
    capabilities: list[Capability]
