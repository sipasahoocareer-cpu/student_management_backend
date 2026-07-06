"""
MongoDB-backed teacher router.
- GET  /api/mongo/teachers          - Admin: list / search teachers
- POST /api/mongo/teachers          - Admin: add teacher
- PUT  /api/mongo/teachers/{id}     - Admin: edit teacher
- DELETE /api/mongo/teachers/{id}   - Admin: delete teacher
"""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr

from core.mongo_db import get_teachers_collection
from utils.hash_util import hash_password
from .mongo_auth import get_current_mongo_user

router = APIRouter()


class TeacherCreatePayload(BaseModel):
    name: str
    teacher_id: str
    subject: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None


class TeacherUpdatePayload(BaseModel):
    name: Optional[str] = None
    teacher_id: Optional[str] = None
    subject: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password_hash", None)
    return doc


def _generate_teacher_email(teacher_id: str) -> str:
    safe_id = "".join(ch.lower() if ch.isalnum() else "." for ch in teacher_id).strip(".")
    return f"{safe_id or 'teacher'}@teachers.local"


@router.get("/teachers")
async def list_teachers(
    q: Optional[str] = Query(None, description="Search by name, teacher id or subject"),
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_teachers_collection()
    query_filter = {}
    if q:
        import re

        pattern = re.compile(re.escape(q), re.IGNORECASE)
        query_filter = {
            "$or": [
                {"name": {"$regex": pattern}},
                {"teacher_id": {"$regex": pattern}},
                {"subject": {"$regex": pattern}},
            ]
        }

    cursor = col.find(query_filter).sort("created_at", -1)
    teachers = [_serialize(doc) async for doc in cursor]
    return {"success": True, "data": teachers}


@router.post("/teachers")
async def add_teacher(
    payload: TeacherCreatePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_teachers_collection()
    teacher_id = payload.teacher_id.strip().upper()
    name = payload.name.strip()
    password = (payload.password or teacher_id).strip()
    email = payload.email.strip().lower() if payload.email else _generate_teacher_email(teacher_id)

    existing = await col.find_one({"teacher_id": teacher_id})
    if existing:
        raise HTTPException(status_code=400, detail="Teacher ID already exists")

    existing_email = await col.find_one({"email": email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Teacher email already exists")

    doc = {
        "name": name,
        "name_lower": name.lower(),
        "teacher_id": teacher_id,
        "teacher_id_lower": teacher_id.lower(),
        "email": email,
        "email_lower": email,
        "password_hash": hash_password(password),
        "subject": (payload.subject or "").strip(),
        "role": "teacher",
        "created_at": datetime.utcnow(),
    }

    result = await col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    doc.pop("password_hash", None)

    return {"success": True, "data": doc, "login_password": password}


@router.put("/teachers/{teacher_id}")
async def edit_teacher(
    teacher_id: str,
    payload: TeacherUpdatePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_teachers_collection()

    try:
        oid = ObjectId(teacher_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid teacher ID")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "name" in updates:
        updates["name"] = updates["name"].strip()
        updates["name_lower"] = updates["name"].lower()

    if "email" in updates:
        updates["email"] = updates["email"].strip().lower()
        if not updates["email"]:
            raise HTTPException(status_code=400, detail="Email cannot be empty")
        updates["email_lower"] = updates["email"]
        existing_email = await col.find_one({"email_lower": updates["email_lower"], "_id": {"$ne": oid}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")

    if "teacher_id" in updates:
        new_teacher_id = updates["teacher_id"].strip().upper()
        updates["teacher_id"] = new_teacher_id
        updates["teacher_id_lower"] = new_teacher_id.lower()
        if "password" not in updates:
            updates["password_hash"] = hash_password(new_teacher_id)

    if "password" in updates:
        updates["password_hash"] = hash_password(updates.pop("password").strip())

    updates.pop("password", None)

    result = await col.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")

    updated = await col.find_one({"_id": oid})
    return {"success": True, "data": _serialize(updated)}


@router.delete("/teachers/{teacher_id}")
async def delete_teacher(
    teacher_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_teachers_collection()

    try:
        oid = ObjectId(teacher_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid teacher ID")

    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {"success": True, "message": "Teacher deleted"}
