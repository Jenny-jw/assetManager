from __future__ import annotations

from enum import Enum
from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator
import yaml

from models.tenant import Tenant

class Edition(str, Enum):
    personal = "personal"
    professional = "professional"

class Locale(str, Enum):
    zh_tw = "zh-TW"
    en = "en"

ALLOWED_ROLES = frozenset({"owner"})

PERSONAL_DASHBOARD_WIDGETS = frozenset(
    {"summary", "origin", "genre", "recent_assets"}
)
ORDER_DASHBOARD_WIDGETS = frozenset({"pending_orders"})
PROFIT_DASHBOARD_WIDGETS = frozenset({"profit"})

class DeploymentModules(BaseModel):
    inventory: bool = True
    dashboard_summary: bool = True
    dashboard_origin_chart: bool = True
    dashboard_genre_chart: bool = True
    dashboard_recent_assets: bool = True
    orders: bool = False
    order_notifications: bool = False
    pricing_visibility: bool = True
    profit_analytics: bool = False

class DeploymentConfig(BaseModel):
    edition: Edition
    locale: Locale
    roles_enabled: list[str] = Field(default_factory=lambda: ["owner"])
    modules: DeploymentModules
    dashboard_layout: list[str] = Field(min_length=1)

    @field_validator("roles_enabled")
    @classmethod
    def roles_must_be_allowed(cls, roles: list[str]) -> list[str]:
        if not roles:
            raise ValueError("roles_enabled must not be empty")
        unknown = set(roles) - ALLOWED_ROLES
        if unknown:
            raise ValueError(f"unsupported roles: {sorted(unknown)}")
        return roles

    @model_validator(mode="after")
    def validate_edition_rules(self) -> DeploymentConfig:
        if self.edition is Edition.personal and self.modules.orders:
            raise ValueError("personal edition requires modules.orders to be false")
        if self.edition is Edition.personal and self.modules.order_notifications:
            raise ValueError("personal edition requires modules.order_notifications to be false")
        if self.edition is Edition.personal and self.modules.profit_analytics:
            raise ValueError("personal edition requires modules.profit_analytics to be false")
        if self.modules.order_notifications and not self.modules.orders:
            raise ValueError("order_notifications requires modules.orders to be true")
        layout = set(self.dashboard_layout)
        if self.edition is Edition.personal and layout & ORDER_DASHBOARD_WIDGETS:
            raise ValueError(
                "personal edition cannot include order widgets in dashboard_layout"
            )
        if self.edition is Edition.personal:
            unknown = layout - PERSONAL_DASHBOARD_WIDGETS
            if unknown:
                raise ValueError(
                    f"personal edition has unsupported dashboard widgets: {sorted(unknown)}"
                )
        if not self.modules.orders and layout & ORDER_DASHBOARD_WIDGETS:
            raise ValueError(
                "dashboard_layout cannot include pending_orders when modules.orders is false"
            )
        if not self.modules.profit_analytics and layout & PROFIT_DASHBOARD_WIDGETS:
            raise ValueError(
                "dashboard_layout cannot include profit when modules.profit_analytics is false"
            )
        return self

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def default_config_path() -> Path:
    return _repo_root() / "deploy" / "config.yaml"

def personal_preset_path() -> Path:
    return _repo_root() / "deploy" / "presets" / "personal.yaml"

def professional_preset_path() -> Path:
    return _repo_root() / "deploy" / "presets" / "professional.yaml"

def load_personal_preset() -> DeploymentConfig:
    return load_deployment_config(personal_preset_path())

def load_professional_preset() -> DeploymentConfig:
    return load_deployment_config(professional_preset_path())

def load_preset_for_edition(edition: Edition) -> DeploymentConfig:
    if edition is Edition.professional:
        return load_professional_preset()
    return load_personal_preset()

def resolve_config_path() -> Path:
    override = os.getenv("DEPLOY_CONFIG_PATH")
    if override:
        path = Path(override).expanduser()
        if not path.is_absolute():
            path = _repo_root() / path
        return path.resolve()
    return default_config_path()

def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"deployment config not found: {path}")
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"deployment config must be a mapping: {path}")
    return data

def load_deployment_config(path: Path | None = None) -> DeploymentConfig:
    config_path = path if path is not None else resolve_config_path()
    return DeploymentConfig.model_validate(_load_yaml(config_path))

def deployment_from_tenant(tenant: Tenant) -> DeploymentConfig:
    return DeploymentConfig.model_validate(
        {
            "edition": tenant.edition,
            "locale": tenant.locale,
            "roles_enabled": tenant.roles_enabled,
            "modules": tenant.modules,
            "dashboard_layout": tenant.dashboard_layout,
        }
    )

@lru_cache
def get_deployment() -> DeploymentConfig:
    return load_deployment_config()

def reset_deployment_cache() -> None:
    get_deployment.cache_clear()
