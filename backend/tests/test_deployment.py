from pathlib import Path

import pytest
from pydantic import ValidationError

from core.deployment import (
    Edition,
    Locale,
    get_deployment,
    load_deployment_config,
    load_personal_preset,
    personal_preset_path,
    reset_deployment_cache,
    resolve_config_path,
)

@pytest.fixture(autouse=True)
def clear_deployment_cache():
    reset_deployment_cache()
    yield
    reset_deployment_cache()

def test_load_repo_config_yaml():
    config = load_deployment_config()
    assert config.edition is Edition.personal
    assert config.locale is Locale.zh_tw
    assert config.modules.orders is False
    assert config.modules.order_notifications is False
    assert config.modules.profit_analytics is False
    assert config.roles_enabled == ["owner"]
    assert "summary" in config.dashboard_layout
    assert "pending_orders" not in config.dashboard_layout

def test_default_config_matches_personal_preset():
    default_config = load_deployment_config()
    personal_preset = load_personal_preset()
    assert default_config.model_dump() == personal_preset.model_dump()

def test_get_deployment_uses_personal_default(monkeypatch):
    monkeypatch.delenv("DEPLOY_CONFIG_PATH", raising=False)
    deployment = get_deployment()
    assert deployment.edition is Edition.personal
    assert deployment.modules.orders is False

def test_personal_preset_path_points_at_repo_file():
    path = personal_preset_path()
    assert path.name == "personal.yaml"
    assert path.is_file()

def test_relative_deploy_config_path_is_repo_root_relative(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("DEPLOY_CONFIG_PATH", "deploy/config.yaml")
    assert resolve_config_path() == (repo_root / "deploy" / "config.yaml").resolve()

def test_load_personal_preset():
    path = Path(__file__).resolve().parents[2] / "deploy" / "presets" / "personal.yaml"
    config = load_deployment_config(path)
    assert config.edition is Edition.personal
    assert config.modules.profit_analytics is False
    assert config.roles_enabled == ["owner"]

def test_load_professional_preset():
    path = Path(__file__).resolve().parents[2] / "deploy" / "presets" / "professional.yaml"
    config = load_deployment_config(path)
    assert config.edition is Edition.professional
    assert config.modules.orders is True
    assert config.modules.profit_analytics is True

def test_personal_edition_rejects_orders_enabled(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        """
edition: personal
locale: zh-TW
roles_enabled:
  - owner
modules:
  inventory: true
  dashboard_summary: true
  dashboard_origin_chart: true
  dashboard_genre_chart: true
  dashboard_recent_assets: true
  orders: true
  order_notifications: false
  pricing_visibility: true
  profit_analytics: false
dashboard_layout:
  - summary
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_deployment_config(config_file)

def test_personal_edition_rejects_pending_orders_widget(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        """
edition: personal
locale: zh-TW
roles_enabled:
  - owner
modules:
  inventory: true
  dashboard_summary: true
  dashboard_origin_chart: true
  dashboard_genre_chart: true
  dashboard_recent_assets: true
  orders: false
  order_notifications: false
  pricing_visibility: true
  profit_analytics: false
dashboard_layout:
  - summary
  - pending_orders
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_deployment_config(config_file)

def test_rejects_unsupported_role(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        """
edition: personal
locale: en
roles_enabled:
  - customer
modules:
  inventory: true
  dashboard_summary: true
  dashboard_origin_chart: true
  dashboard_genre_chart: true
  dashboard_recent_assets: true
  orders: false
  order_notifications: false
  pricing_visibility: true
  profit_analytics: false
dashboard_layout:
  - summary
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_deployment_config(config_file)
