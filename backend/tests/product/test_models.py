import models  # noqa: F401
from core.db import Base
from models.stock import Stock
from models.user import User

def test_product_tables_registered():
    table_names = set(Base.metadata.tables)
    assert "users" in table_names
    assert "stocks" in table_names

def test_users_table_has_username_unique():
    username = User.__table__.c.username
    assert username.unique is True

def test_stocks_table_allows_null_genre_and_origin():
    assert Stock.__table__.c.genre.nullable is True
    assert Stock.__table__.c.origin.nullable is True

def test_stocks_table_has_soft_delete_column():
    assert Stock.__table__.c.deleted_at.nullable is True
