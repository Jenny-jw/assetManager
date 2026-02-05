from fastapi import APIRouter
from models.tea import Tea
from db import db

router = APIRouter(prefix="/tea", tags=["Tea"])

@router.post("/")
async def create_tea(tea: Tea):
    tea_dict = tea.model_dump()
    result = db.teas.insert_one(tea_dict)
    
    return {
        "message": "Tea created",
        "tea": tea_dict,
        "id": str(result.inserted_id)
    }