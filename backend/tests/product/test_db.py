import pytest
from sqlalchemy.exc import SQLAlchemyError

from core.db import get_db, get_engine, ping_postgres, reset_db_state_for_tests

@pytest.fixture(autouse=True)
def reset_engine():
    reset_db_state_for_tests()
    yield
    reset_db_state_for_tests()

def test_get_engine_requires_postgres_url(monkeypatch):
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    with pytest.raises(RuntimeError, match="POSTGRES_URL is required"):
        get_engine()

def test_ping_postgres_executes_select(monkeypatch):
    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgresql+psycopg://ci:ci@localhost:5432/ci_test",
    )
    calls: list[str] = []

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, statement):
            calls.append(str(statement))

    class FakeEngine:
        def connect(self):
            return FakeConnection()

        def dispose(self):
            return None

    monkeypatch.setattr("core.db.create_engine", lambda *args, **kwargs: FakeEngine())
    ping_postgres()
    assert calls

def test_ping_postgres_propagates_db_errors(monkeypatch):
    monkeypatch.setenv(
        "POSTGRES_URL",
        "postgresql+psycopg://ci:ci@localhost:5432/ci_test",
    )

    class FakeEngine:
        def connect(self):
            raise SQLAlchemyError("down")

        def dispose(self):
            return None

    monkeypatch.setattr("core.db.create_engine", lambda *args, **kwargs: FakeEngine())
    with pytest.raises(SQLAlchemyError):
        ping_postgres()

def test_get_db_yields_session_and_closes(monkeypatch):
    closed: list[bool] = []

    class FakeSession:
        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr("core.db.get_session_factory", lambda: lambda: FakeSession())
    generator = get_db()
    session = next(generator)
    assert isinstance(session, FakeSession)
    with pytest.raises(StopIteration):
        generator.send(None)
    assert closed == [True]
