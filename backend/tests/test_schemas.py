import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.deployment import Edition
from models.stock import Stock
from models.user import User
from schemas.stock import (
    StockCreate,
    StockResponse,
    validate_weight_grams_for_edition,
)
from schemas.user import UserCreate, UserLogin, UserResponse

def test_user_create_allows_null_email():
    user = UserCreate(
        username="farmer01",
        name="陳伯伯",
        email=None,
        password="secretpass",
    )
    assert user.email is None

def test_user_login_uses_username():
    login = UserLogin(username="farmer01", password="secretpass")
    assert login.username == "farmer01"

def test_stock_create_allows_null_genre_and_origin():
    stock = StockCreate(name="高山烏龍")
    assert stock.genre is None
    assert stock.origin is None

def test_stock_create_rejects_non_positive_weight():
    with pytest.raises(ValidationError):
        StockCreate(name="Test", weight_grams=0)

def test_validate_weight_grams_personal_only_75_or_150():
    assert validate_weight_grams_for_edition(75, Edition.personal) == 75
    assert validate_weight_grams_for_edition(150, Edition.personal) == 150
    with pytest.raises(ValueError, match="75 or 150"):
        validate_weight_grams_for_edition(100, Edition.personal)

def test_validate_weight_grams_professional_allows_any_positive():
    assert validate_weight_grams_for_edition(100, Edition.professional) == 100

def test_stock_response_from_orm():
    now = datetime.now(timezone.utc)
    row = Stock(
        id=uuid.uuid4(),
        name="Test",
        quantity=2,
        created_at=now,
    )
    response = StockResponse.model_validate(row)
    assert response.name == "Test"
    assert response.id == str(row.id)

def test_user_response_from_orm():
    now = datetime.now(timezone.utc)
    row = User(
        id=uuid.uuid4(),
        username="owner1",
        name="Owner",
        hashed_password="hashed",
        role="owner",
        is_active=True,
        created_at=now,
    )
    response = UserResponse.model_validate(row)
    assert response.username == "owner1"
    assert response.role == "owner"
