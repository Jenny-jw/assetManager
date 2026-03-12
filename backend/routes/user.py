from fastapi import APIRouter
from models.user import User
from db import db

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/", response_model=User)
def create_user(user: User):
    user_dict = user.model_dump()
    result = db.users.insert_one(user_dict)
    user_dict['id'] = str(result.inserted_id)
    return user_dict