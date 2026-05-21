from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from schemas.tea import TeaCreate, TeaResponsePublic, TeaResponseList, TeaUpdate
from core.db import db
from bson.objectid import ObjectId
from pymongo import ReturnDocument
from starlette.status import HTTP_206_PARTIAL_CONTENT
import json
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tea", tags=["Tea"])

@router.post("/", response_model=TeaResponsePublic)
def create_tea(tea: TeaCreate):
    tea_dict = tea.model_dump()
    result = db.teas.insert_one(tea_dict)
    tea_dict["id"] = str(result.inserted_id)
    return tea_dict

@router.get("/", response_model=TeaResponseList)
def list_teas():
    teas = db.teas.find()
    result = []
    errors = []
    for i, tea in enumerate(teas):
        if not isinstance(tea, dict):
            errors.append({"index": i, "id": None, "error": "not a dict"})
            logger.warning("Non-dict tea at index %s: %r", i, tea)
            continue
        required = ["name", "genre"]
        if not all(field in tea for field in required):
            errors.append(f"Missing fields in tea at index {i}, id={tea.get('_id')}")
            logger.warning("Missing fields for tea id=%s missing=%s", tea.get("_id"), tea)
            continue
        try:
            tea["id"] = str(tea["_id"])
            tea["created_at"] = tea.get("created_at")
            tea.pop("_id", None)
            tr = TeaResponsePublic.model_validate(tea)
            result.append(tr)
        except Exception as e:
            errors.append({"index": i, "id": str(tea.get("_id")), "error": str(e)})
            logger.exception("Failed to build TeaResponsePublic for tea id=%s", tea.get("_id"))
            continue
    
    status_code = HTTP_206_PARTIAL_CONTENT if errors else status.HTTP_200_OK
    data = [json.loads(t.json()) for t in result]   # Pydantic 會把 datetime 序列化為 ISO string
    return JSONResponse(content={"data": data, "errors": errors}, status_code=status_code)

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