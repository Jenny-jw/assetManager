from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

class Edition(str, Enum):
    personal = "personal"
    professional = "professional"

class Locale(str, Enum):
    zh_tw = "zh-TW"
    en = "en"

ALLOWED_ROLES = frozenset({"owner"})

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
        return self

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def default_config_path() -> Path:
    return _repo_root() / "deploy" / "config.yaml"

def resolve_config_path() -> Path:
    override = os.getenv("DEPLOY_CONFIG_PATH")
    if override:
        return Path(override).expanduser().resolve()
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

@lru_cache
def get_deployment() -> DeploymentConfig:
    return load_deployment_config()

def reset_deployment_cache() -> None:
    get_deployment.cache_clear()
