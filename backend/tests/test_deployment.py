from pathlib import Path

from pydantic import ValidationError
import pytest

from core.deployment import (
    Edition,
    Locale,
    get_deployment,
    load_deployment_config,
    load_personal_preset,
    load_preset_for_edition,
    load_professional_preset,
    personal_preset_path,
    reset_deployment_cache,
    resolve_config_path,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]

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
    monkeypatch.setenv("DEPLOY_CONFIG_PATH", "deploy/config.yaml")
    assert resolve_config_path() == (_REPO_ROOT / "deploy" / "config.yaml").resolve()

def test_load_personal_preset():
    config = load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "personal.yaml")
    assert config.edition is Edition.personal
    assert config.modules.profit_analytics is False
    assert config.roles_enabled == ["owner"]

def test_load_professional_preset():
    config = load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "professional.yaml")
    assert config.edition is Edition.professional
    assert config.modules.orders is True
    assert config.modules.profit_analytics is True
    assert "profit" in config.dashboard_layout

def test_load_preset_for_edition_selects_professional_yaml():
    professional = load_preset_for_edition(Edition.professional)
    assert professional.model_dump() == load_professional_preset().model_dump()
    assert professional.modules.orders is True
    assert professional.modules.profit_analytics is True

    personal = load_preset_for_edition(Edition.personal)
    assert personal.model_dump() == load_personal_preset().model_dump()
    assert personal.modules.orders is False

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

def test_personal_edition_rejects_profit_widget(tmp_path):
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
  - profit
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_deployment_config(config_file)

def test_rejects_profit_widget_when_module_off(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        """
edition: professional
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
  order_notifications: true
  pricing_visibility: true
  profit_analytics: false
dashboard_layout:
  - summary
  - profit
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
