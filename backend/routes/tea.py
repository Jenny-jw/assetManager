from fastapi import APIRouter, status, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from schemas.tea import TeaCreate, TeaResponsePublic, TeaResponseList, TeaUpdate
from core.db import db
from bson.objectid import ObjectId
from pymongo import ReturnDocument
from starlette.status import HTTP_206_PARTIAL_CONTENT
from dependencies.auth import get_current_user, require_role
from models.user import UserRole
from datetime import datetime, timezone
import json
import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tea",
    tags=["Tea"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/", response_model=TeaResponsePublic)
def create_tea(tea: TeaCreate, _: dict = Depends(require_role(UserRole.admin))):
    tea_dict = tea.model_dump()
    result = db.teas.insert_one(tea_dict)
    tea_dict["id"] = str(result.inserted_id)
    return tea_dict

@router.get("/", response_model=TeaResponseList)
def list_teas(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    genre: str | None = None,
    origin: str | None = None,
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|name|genre|origin|quantity|score|price|harvest_time)$",
    ),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
):
    filters = {}
    if search:
        filters["$text"] = {"$search": search}
    if genre:
        filters["genre"] = genre
    if origin:
        filters["origin"] = origin

    skip = (page - 1) * limit
    direction = 1 if sort_direction == "asc" else -1
    total = db.teas.count_documents(filters)
    teas = db.teas.find(filters).sort(sort_by, direction).skip(skip).limit(limit)
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
    return JSONResponse(
        content={
            "data": data,
            "page": page,
            "limit": limit,
            "total": total,
            "errors": errors,
        },
        status_code=status_code,
    )

@router.get("/{tea_id}", response_model=TeaResponsePublic)
def get_tea(tea_id: str):
    if not ObjectId.is_valid(tea_id):
        raise HTTPException(status_code=400, detail="Invalid tea id")

    tea = db.teas.find_one({"_id": ObjectId(tea_id)})

    if not tea:
        raise HTTPException(status_code=404, detail="Tea not found")

    tea["id"] = str(tea["_id"])
    tea.pop("_id", None)

    return tea

@router.patch("/{tea_id}", response_model=TeaResponsePublic)
def edit_tea(
    tea_id: str,
    tea: TeaUpdate,
    _: dict = Depends(require_role(UserRole.admin)),
):
    if not ObjectId.is_valid(tea_id):
        raise HTTPException(status_code=400, detail="Invalid tea id")

    update_data = tea.model_dump(exclude_unset=True)

    for key in ("origin", "producer", "comment"):
        if key in update_data and update_data[key] == "":
            update_data[key] = None

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_data = {k: v for k, v in update_data.items() if v is not None}
    unset_data = {k: "" for k, v in update_data.items() if v is None}

    update_ops: dict = {}
    if set_data:
        set_data["updated_at"] = datetime.now(timezone.utc)
        update_ops["$set"] = set_data
    elif unset_data:
        update_ops["$set"] = {"updated_at": datetime.now(timezone.utc)}
    if unset_data:
        update_ops["$unset"] = unset_data

    updated = db.teas.find_one_and_update(
        {"_id": ObjectId(tea_id)},
        update_ops,
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Tea not found")

    updated["id"] = str(updated["_id"])
    updated.pop("_id", None)

    return updated

@router.delete("/{tea_id}")
def remove_tea(tea_id: str, _: dict = Depends(require_role(UserRole.admin))):
    if not ObjectId.is_valid(tea_id):
        raise HTTPException(status_code=400, detail="Invalid tea id")

    res = db.teas.delete_one({"_id": ObjectId(tea_id)})

    if (res.deleted_count == 1):
        return {"message": "Tea deleted"}

    raise HTTPException(status_code=404, detail="Tea not found")