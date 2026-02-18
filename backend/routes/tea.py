from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from models.tea import TeaCreate, TeaResponse, TeaUpdate
from db import db
from bson.objectid import ObjectId
from pymongo import ReturnDocument

router = APIRouter(prefix="/tea", tags=["Tea"])

@router.post("/", response_model=TeaResponse)
def create_tea(tea: TeaCreate):
    tea_dict = tea.model_dump()
    result = db.teas.insert_one(tea_dict)
    tea_dict["id"] = str(result.inserted_id) # type: bson.ObjectId
    return tea_dict

@router.get("/", response_model=list[TeaResponse])
def list_teas():
    teas = db.teas.find()
    return [
        TeaResponse(
            id=str(tea["_id"]),
            name=tea["name"],
            origin=tea["origin"],
            roastLevel=tea["roastLevel"],
            harvestTime=tea["harvestTime"],
            weight=tea["weight"],
            quantity=tea["quantity"]
        )
        for tea in teas
    ]

@router.patch("/{tea_id}")
def edit_tea(tea_id: str, tea: TeaUpdate):
    update_data = tea.model_dump(exclude_unset=True, exclude_none=True)
    
    if not update_data:
        return {"message": "No fields to update"}
    
    updated = db.teas.find_one_and_update(
        {"_id": ObjectId(tea_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    
    if not updated:
        return {"message": "Tea not found"}
    
    updated["id"] = str(updated["_id"])
    
    return updated

@router.delete("/{tea_id}")
def remove_tea(tea_id: str):
    res = db.teas.delete_one({"_id": ObjectId(tea_id)})
    
    if (res.deleted_count == 1):
        return {"message": "Tea deleted"}
    else:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": "Tea not found"})