# /login、/signup、/logout
from fastapi import APIRouter, HTTPException, Response
from schemas.user import UserLogin, UserCreate, UserResponse
from core.db import db
from core.security import hash_password, verify_password, create_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=UserResponse)
def signup(user: UserCreate):
    existing_user = db.users.find_one({"email": user.email})
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user.model_dump()
    hashed_pwd = hash_password(user_dict.pop("password"))
    user_dict["hashed_password"] = hashed_pwd
    user_dict["created_at"] = datetime.now()
    user_dict["role"] = "user"
    user_dict["is_active"] = True
    result = db.users.insert_one(user_dict)
    user_dict['id'] = str(result.inserted_id)
    
    return user_dict 

@router.post("/login")
def login(user: UserLogin, response: Response):
    db_user = db.users.find_one({"email": user.email})
    
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token({"sub": str(db_user["_id"]), "role": db_user["role"]})
    response.set_cookie(key="token", value=token, httponly=True)
    
    return {"message": "Login successful"}

# @router.post("/logout")