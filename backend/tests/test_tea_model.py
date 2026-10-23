import pytest
from pydantic import ValidationError

from models.tea import TeaInDB

def test_tea_in_db_does_not_mint_an_id_and_requires_package_fields():
    tea = TeaInDB(name="Alishan", genre="Oolong", weight=150, quantity=2)

    assert tea.id is None
    assert tea.owner_id is None
    assert "deleted_at" not in TeaInDB.model_fields

    with pytest.raises(ValidationError):
        TeaInDB(name="Alishan", genre="Oolong", quantity=2)

    with pytest.raises(ValidationError):
        TeaInDB(name="Alishan", genre="Oolong", weight=100, quantity=1)

    with pytest.raises(ValidationError):
        TeaInDB(name="Alishan", genre="Oolong", weight=150, quantity=0)