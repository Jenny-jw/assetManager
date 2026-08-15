from sqlalchemy import UniqueConstraint, create_engine
from sqlalchemy.orm import Session

from core.db import Base
import models  # noqa: F401
from models.order import Order, OrderItem, StockMovement
from models.stock import Stock
from models.tenant import Tenant
from models.user import User

def test_product_tables_registered():
    table_names = set(Base.metadata.tables)
    assert "tenants" in table_names
    assert "users" in table_names
    assert "stocks" in table_names
    assert "orders" in table_names
    assert "order_items" in table_names
    assert "stock_movements" in table_names

def test_tenants_table_has_saas_configuration_columns():
    columns = set(Tenant.__table__.c.keys())
    assert {
        "slug",
        "edition",
        "locale",
        "roles_enabled",
        "modules",
        "dashboard_layout",
        "status",
        "trial_ends_at",
    } <= columns

def test_tenant_json_config_tracks_in_place_changes():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Tenant.__table__.create(bind=engine)
    with Session(engine) as session:
        tenant = Tenant(
            slug="sample-shop",
            edition="personal",
            locale="zh-TW",
            roles_enabled=["owner"],
            modules={"inventory": True, "orders": False},
            dashboard_layout=["summary"],
            status="active",
        )
        session.add(tenant)
        session.commit()

        tenant.modules["orders"] = True
        session.commit()
        session.expire(tenant)

        assert tenant.modules["orders"] is True
    Tenant.__table__.drop(bind=engine)
    engine.dispose()

def test_users_table_has_tenant_scoped_unique_constraints():
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in User.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("tenant_id", "username") in unique_columns
    assert ("tenant_id", "email") in unique_columns
    assert User.__table__.c.username.unique is not True

def test_users_table_allows_only_one_owner_per_tenant():
    owner_index = next(
        index
        for index in User.__table__.indexes
        if index.name == "uq_users_one_owner_per_tenant"
    )
    assert owner_index.unique is True
    assert str(owner_index.dialect_options["postgresql"]["where"]) == "role = 'owner'"

def test_user_and_stock_reference_tenants():
    user_foreign_key = next(iter(User.__table__.c.tenant_id.foreign_keys))
    stock_foreign_key = next(iter(Stock.__table__.c.tenant_id.foreign_keys))
    assert user_foreign_key.target_fullname == "tenants.id"
    assert stock_foreign_key.target_fullname == "tenants.id"

def test_tenant_ids_are_required_after_contract_migration():
    assert User.__table__.c.tenant_id.nullable is False
    assert Stock.__table__.c.tenant_id.nullable is False
    assert Order.__table__.c.tenant_id.nullable is False
    assert OrderItem.__table__.c.tenant_id.nullable is False
    assert StockMovement.__table__.c.tenant_id.nullable is False

def test_stocks_table_allows_null_genre_and_origin():
    assert Stock.__table__.c.genre.nullable is True
    assert Stock.__table__.c.origin.nullable is True

def test_stocks_table_has_soft_delete_column():
    assert Stock.__table__.c.deleted_at.nullable is True
