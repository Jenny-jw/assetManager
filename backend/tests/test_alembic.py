from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]

def test_alembic_scaffold_present():
    assert (_BACKEND_ROOT / "alembic.ini").is_file()
    assert (_BACKEND_ROOT / "alembic" / "env.py").is_file()
    assert (_BACKEND_ROOT / "alembic" / "script.py.mako").is_file()
    assert (_BACKEND_ROOT / "alembic" / "versions").is_dir()
    migrations = list((_BACKEND_ROOT / "alembic" / "versions").glob("*.py"))
    assert migrations, "expected at least one migration revision"

def test_alembic_env_wires_base_metadata(monkeypatch):
    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgresql+psycopg://ci:ci@localhost:5432/ci_test",
    )
    from core.db import Base

    env_source = (_BACKEND_ROOT / "alembic" / "env.py").read_text(encoding="utf-8")
    assert "target_metadata = Base.metadata" in env_source
    assert "import models" in env_source
    assert Base.metadata is not None

def test_tenant_migration_follows_initial_schema():
    migration = (
        _BACKEND_ROOT
        / "alembic"
        / "versions"
        / "8f3a1c7d2e4b_add_tenant_foundation.py"
    )
    source = migration.read_text(encoding="utf-8")

    assert 'revision: str = "8f3a1c7d2e4b"' in source
    assert 'down_revision: Union[str, None] = "b7c4e2a91d30"' in source
    assert '"tenants"' in source
    assert '"tenant_id"' in source

def test_contract_tenant_id_migration_follows_expand_phase():
    migration = (
        _BACKEND_ROOT
        / "alembic"
        / "versions"
        / "d2064bf95049_contract_tenant_id_not_null.py"
    )
    source = migration.read_text(encoding="utf-8")

    assert 'revision: str = "d2064bf95049"' in source
    assert 'down_revision: Union[str, None] = "8f3a1c7d2e4b"' in source
    assert "_backfill_orphan_tenant_ids" in source
    assert 'op.alter_column(\n        "users"' in source
    assert 'op.alter_column(\n        "stocks"' in source
    assert "nullable=False" in source
    assert "legacy-bootstrap" in source

def test_stock_cost_migration_follows_orders_tables():
    migration = (
        _BACKEND_ROOT
        / "alembic"
        / "versions"
        / "e1a7b9c04d18_add_stock_cost_per_jin.py"
    )
    source = migration.read_text(encoding="utf-8")

    assert 'revision: str = "e1a7b9c04d18"' in source
    assert 'down_revision: str | None = "c9e2f4a81b07"' in source
    assert "cost_per_jin" in source

def test_orders_migration_follows_tenant_id_contract():
    migration = (
        _BACKEND_ROOT
        / "alembic"
        / "versions"
        / "c9e2f4a81b07_add_orders_tables.py"
    )
    source = migration.read_text(encoding="utf-8")

    assert 'revision: str = "c9e2f4a81b07"' in source
    assert 'down_revision: str | None = "d2064bf95049"' in source
    assert '"orders"' in source
    assert '"order_items"' in source
    assert '"stock_movements"' in source
    assert "tenant_id" in source
