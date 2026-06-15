from pathlib import Path

import pytest
from pydantic import ValidationError

from core.deployment import (
    Edition,
    Locale,
    load_deployment_config,
    reset_deployment_cache,
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
    assert "summary" in config.dashboard_layout

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
