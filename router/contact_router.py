"""
Contact Us / Query router (MongoDB-backed).
- POST   /api/mongo/contact              – Public: submit a query
- GET    /api/mongo/contact              – Admin: list all queries
- PATCH  /api/mongo/contact/{id}/resolve – Admin: mark as resolved
- DELETE /api/mongo/contact/{id}         – Admin: delete a query
"""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.mongo_db import get_queries_collection
from .mongo_auth import get_current_mongo_user

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class QuerySubmitPayload(BaseModel):
    name: str
    email: Optional[str] = ""
    subject: str
    message: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("submitted_at"), datetime):
        doc["submitted_at"] = doc["submitted_at"].isoformat()
    return doc


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/contact")
async def submit_query(payload: QuerySubmitPayload):
    """Public endpoint – anyone can submit a contact query."""
    col = get_queries_collection()
    doc = {
        "name": payload.name.strip(),
        "email": payload.email.strip().lower(),
        "subject": payload.subject.strip(),
        "message": payload.message.strip(),
        "status": "pending",
        "submitted_at": datetime.utcnow(),
    }
    result = await col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return {"success": True, "data": doc, "message": "Query submitted successfully"}


@router.get("/contact")
async def list_queries(current_user: dict = Depends(get_current_mongo_user)):
    """Admin: get all contact queries, newest first."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_queries_collection()
    cursor = col.find({}).sort("submitted_at", -1)
    queries = [_serialize(doc) async for doc in cursor]
    return {"success": True, "data": queries}


@router.patch("/contact/{query_id}/resolve")
async def resolve_query(
    query_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    """Admin: toggle a query's status between pending and resolved."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_queries_collection()
    try:
        oid = ObjectId(query_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query ID")

    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Query not found")

    new_status = "resolved" if doc.get("status") == "pending" else "pending"
    await col.update_one({"_id": oid}, {"$set": {"status": new_status}})

    updated = await col.find_one({"_id": oid})
    return {"success": True, "data": _serialize(updated)}


@router.delete("/contact/{query_id}")
async def delete_query(
    query_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    """Admin: permanently delete a contact query."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_queries_collection()
    try:
        oid = ObjectId(query_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid query ID")

    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Query not found")

    return {"success": True, "message": "Query deleted"}


@router.get("/contact/stats")
async def query_stats(current_user: dict = Depends(get_current_mongo_user)):
    """Admin: count of pending queries."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_queries_collection()
    pending = await col.count_documents({"status": "pending"})
    total = await col.count_documents({})
    return {"success": True, "pending": pending, "total": total}
