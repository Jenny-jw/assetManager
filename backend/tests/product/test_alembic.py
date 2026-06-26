from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[2]

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
