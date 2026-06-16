from pathlib import Path

def test_alembic_scaffold_present():
    backend = Path(__file__).resolve().parents[1]
    assert (backend / "alembic.ini").is_file()
    assert (backend / "alembic" / "env.py").is_file()
    assert (backend / "alembic" / "script.py.mako").is_file()
    assert (backend / "alembic" / "versions").is_dir()

def test_alembic_env_wires_base_metadata(monkeypatch):
    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgresql+psycopg://ci:ci@localhost:5432/ci_test",
    )
    from core.db import Base

    backend = Path(__file__).resolve().parents[1]
    env_source = (backend / "alembic" / "env.py").read_text(encoding="utf-8")
    assert "target_metadata = Base.metadata" in env_source
    assert "import models.product" in env_source
    assert Base.metadata is not None