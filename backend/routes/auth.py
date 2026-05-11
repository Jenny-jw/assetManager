# /login、/signup、/logout
from fastapi import APIRouter, HTTPException, Response, Request
from schemas.user import UserLogin, UserCreate, UserResponse
from core.db import db
from passlib.hash import bcrypt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(pwd_input, hashed):
    return pwd_context.verify(pwd_input, hashed)

def create_token(data: dict):
    payload = data.copy()
    expiredAt = datetime.now(datetime.UTC) + timedelta(hours=1)
    payload.update({"exp": expiredAt})
   
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

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

@router.post("/logout")

@router.get("/me", response_model=UserResponse)
def get_current_user(request: Request):
    token = request.cookies.get("token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    user_id = payload.get("sub")
    current_user = db.users.find_one({"_id": user_id})
    
    if not current_user:
        return HTTPException(status_code=404, detail="User not found")
    
    current_user["id"] = str(current_user["_id"])
    
    return current_user