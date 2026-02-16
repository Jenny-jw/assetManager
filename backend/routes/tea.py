from fastapi import APIRouter
from models.tea import Tea
from db import db

router = APIRouter(prefix="/tea", tags=["Tea"])

@router.post("/")
def create_tea(tea: Tea):
    tea_dict = tea.model_dump()
    result = db.teas.insert_one(tea_dict)
    tea_dict['_id'] = str(result.inserted_id)
    
    return {
        "message": "Tea created",
        "tea": tea_dict,
        "id": str(result.inserted_id)
    }

@router.get("/", response_model=list[Tea])
def list_teas():
    return list(db.teas.find())

@router.patch("/")
def edit_tea():
    return

@router.delete("/")
def remove_tea():
    return