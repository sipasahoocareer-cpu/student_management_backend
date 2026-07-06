"""
MongoDB-backed student router.
- POST /api/mongo/auth/login        - Student login (email + password)
- GET  /api/mongo/students          - Admin: list / search students
- POST /api/mongo/students          - Admin: add student
- PUT  /api/mongo/students/{id}     - Admin: edit student
- DELETE /api/mongo/students/{id}   - Admin: delete student
"""
import os
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from core.mongo_db import (
    get_admins_collection,
    get_students_collection,
    get_teachers_collection,
)
from utils.hash_util import hash_password, verify_password
from .mongo_auth import create_token, get_current_mongo_user

router = APIRouter()


class StudentLoginPayload(BaseModel):
    identifier: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    password: str


class StudentCreatePayload(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    password: str = Field(min_length=4)
    class_name: str
    registration_number: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    contact_number: Optional[str] = None


class StudentUpdatePayload(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=4)
    class_name: Optional[str] = None
    registration_number: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    contact_number: Optional[str] = None


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("password_hash", None)
    return doc


def _matches_student_identifier(doc: dict, identifier: str) -> bool:
    if not doc or not identifier:
        return False

    normalized_identifier = identifier.strip().lower()
    for field in ("email", "email_lower", "name", "name_lower", "registration_number", "registration_number_lower"):
        value = doc.get(field)
        if isinstance(value, str) and value.strip().lower() == normalized_identifier:
            return True
    return False


def _get_fallback_admin_payload(identifier: str, password: str) -> Optional[dict]:
    if not identifier or not password:
        return None

    admin_name = (os.getenv("ADMIN_NAME") or "admin").strip()
    admin_password = (os.getenv("ADMIN_PASSWORD") or "admin123").strip()
    if not admin_name or not admin_password:
        return None

    normalized_identifier = identifier.strip().lower()
    normalized_admin_name = admin_name.lower()
    if normalized_identifier != normalized_admin_name:
        return None

    if password != admin_password:
        return None

    return {
        "token": create_token({
            "sub": admin_name,
            "role": "admin",
            "name": admin_name,
            "email": "",
        }),
        "id": "fallback-admin",
        "name": admin_name,
        "role": "admin",
    }


@router.post("/auth/login")
async def student_login(payload: StudentLoginPayload):
    """
    Login for admins, teachers, and students.
    Students may sign in with email, registration number or name.
    Teachers may sign in with email, name or teacher ID.
    Admins may sign in with name or email.
    """
    try:
        print(f"[DEBUG] student_login payload: {payload}")
        identifier = (payload.identifier or payload.email or payload.name or "").strip().lower()
        password = payload.password.strip()

        if not identifier:
            raise HTTPException(status_code=400, detail="Email or name is required")

        fallback_admin = _get_fallback_admin_payload(identifier, password)
        if fallback_admin:
            return fallback_admin

        # check admins
        try:
            admins_col = get_admins_collection()
            admin = await admins_col.find_one(
                {
                    "$or": [
                        {"name_lower": identifier},
                        {"email_lower": identifier},
                        {"name": identifier},
                        {"email": identifier},
                    ]
                }
            )
        except Exception as exc:
            print(f"[WARN] Admin lookup failed: {exc}")
            raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc
        if admin:
            admin_password_hash = admin.get("password_hash")
            admin_password_plain = admin.get("password")
            if (admin_password_hash and verify_password(password, admin_password_hash)) or (
                not admin_password_hash and admin_password_plain == password
            ):
                token = create_token({
                    "sub": admin.get("email") or str(admin["_id"]),
                    "role": "admin",
                    "name": admin["name"],
                    "email": admin.get("email", ""),
                })
                return {
                    "token": token,
                    "id": str(admin["_id"]),
                    "name": admin["name"],
                    "role": "admin",
                }
            raise HTTPException(status_code=401, detail="Invalid Name or Password")

        # check teachers
        teachers_col = get_teachers_collection()
        # Match teacher by lowercase fields or raw fields (some documents may not have lowercased copies)
        teacher = await teachers_col.find_one(
            {
                "$or": [
                    {"name_lower": identifier},
                    {"name": identifier},
                    {"teacher_id_lower": identifier},
                    {"teacher_id": identifier},
                    {"email_lower": identifier},
                    {"email": identifier},
                ]
            }
        )
        if teacher:
            teacher_password_hash = teacher.get("password_hash")
            teacher_password_plain = teacher.get("password")
            # Accept password if it matches stored hash, or matches legacy plain password.
            # Also accept common teacher-id variants (upper/lower) against the stored hash
            tid = (teacher.get("teacher_id") or "").strip()
            tid_variants = {tid, tid.lower(), tid.upper()} if tid else set()

            hashed_ok = False
            if teacher_password_hash:
                # direct verify
                if verify_password(password, teacher_password_hash):
                    hashed_ok = True
                else:
                    # try common teacher-id variants as password (admin often sets teacher_id as default password)
                    for v in tid_variants:
                        if v and verify_password(v, teacher_password_hash):
                            hashed_ok = True
                            break

            plain_ok = False
            if not teacher_password_hash:
                plain_ok = teacher_password_plain == password

            if hashed_ok or plain_ok:
                token = create_token({
                    "sub": teacher.get("email") or str(teacher["_id"]),
                    "role": "teacher",
                    "name": teacher["name"],
                    "email": teacher.get("email", ""),
                })
                return {
                    "token": token,
                    "id": str(teacher["_id"]),
                    "name": teacher["name"],
                    "role": "teacher",
                    "teacher_id": teacher.get("teacher_id", ""),
                    "subject": teacher.get("subject", ""),
                }
            raise HTTPException(status_code=401, detail="Invalid Name or Password")

        # check students
        try:
            students_col = get_students_collection()
        except Exception as exc:
            print(f"[WARN] Student lookup setup failed: {exc}")
            raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc
        cursor = students_col.find({})

        student = None
        async for candidate in cursor:
            if not _matches_student_identifier(candidate, identifier):
                continue

            stored_hash = candidate.get("password_hash")
            if stored_hash and verify_password(password, stored_hash):
                student = candidate
                break

            legacy_password = candidate.get("password") or candidate.get("registration_number")
            if not stored_hash and legacy_password == password:
                student = candidate
                break

        if not student:
            raise HTTPException(status_code=401, detail="Invalid Name or Password")

        token = create_token({
            "sub": student.get("email") or str(student["_id"]),
            "role": "student",
            "name": student["name"],
            "email": student.get("email", ""),
            "class_name": student.get("class_name", ""),
            "department": student.get("department", ""),
        })
        return {
            "token": token,
            "id": str(student["_id"]),
            "name": student["name"],
            "role": "student",
            "email": student.get("email", ""),
            "registration_number": student.get("registration_number", ""),
            "department": student.get("department", ""),
            "semester": student.get("semester", ""),
            "class_name": student.get("class_name", ""),
        }
    except Exception:
        import traceback

        traceback.print_exc()
        raise


@router.post("/auth/login-debug")
async def student_login_debug(request: Request):
    """Temporary debug endpoint: logs raw body and headers to help debug client JSON/CORS issues."""
    try:
        raw = await request.body()
        try:
            j = await request.json()
        except Exception:
            j = None
        hdrs = dict(request.headers)
        try:
            raw_text = raw.decode('utf-8')
        except Exception:
            raw_text = None
        return {"ok": True, "headers": hdrs, "raw_len": len(raw), "raw_text": raw_text, "raw_hex": raw.hex(), "json": j}
    except Exception:
        import traceback

        traceback.print_exc()
        raise


@router.get("/students")
async def list_students(
    q: Optional[str] = Query(None, description="Search by name, class, email, reg_no or department"),
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Admin or teacher access required")

    col = get_students_collection()
    query_filter = {}
    if q:
        import re

        pattern = re.compile(re.escape(q), re.IGNORECASE)
        query_filter = {
            "$or": [
                {"name": {"$regex": pattern}},
                {"class_name": {"$regex": pattern}},
                {"email": {"$regex": pattern}},
                {"registration_number": {"$regex": pattern}},
                {"department": {"$regex": pattern}},
                {"semester": {"$regex": pattern}},
                {"contact_number": {"$regex": pattern}},
            ]
        }

    cursor = col.find(query_filter).sort("created_at", -1)
    students = [_serialize(doc) async for doc in cursor]
    return {"success": True, "data": students}


@router.post("/students")
async def add_student(
    payload: StudentCreatePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        col = get_students_collection()
        name = payload.name.strip()
        class_name = payload.class_name.strip().upper()
        generated_id = f"STU{int(datetime.utcnow().timestamp() * 1000)}"
        email = payload.email.strip().lower() if payload.email else f"{generated_id.lower()}@student.local"
        reg_no = payload.registration_number.strip().upper() if payload.registration_number else generated_id
        password = payload.password.strip()

        existing = await col.find_one(
            {"$or": [{"email_lower": email}, {"registration_number_lower": reg_no.lower()}]}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email or registration number already exists")

        doc = {
            "name": name,
            "name_lower": name.lower(),
            "email": email,
            "email_lower": email,
            "registration_number": reg_no,
            "registration_number_lower": reg_no.lower(),
            "password_hash": hash_password(password),
            "class_name": class_name,
            "department": payload.department.strip() if payload.department else class_name,
            "semester": payload.semester.strip() if payload.semester else "",
            "contact_number": payload.contact_number.strip() if payload.contact_number else "",
            "role": "student",
            "created_at": datetime.utcnow(),
        }

        result = await col.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        doc.pop("password_hash", None)

        return {"success": True, "data": doc}
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Failed to create student: {exc}")
        raise HTTPException(status_code=503, detail="Database service unavailable. Please try again later.") from exc


@router.put("/students/{student_id}")
async def edit_student(
    student_id: str,
    payload: StudentUpdatePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_students_collection()

    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "name" in updates:
        updates["name"] = updates["name"].strip()
        updates["name_lower"] = updates["name"].lower()

    if "email" in updates:
        updates["email"] = updates["email"].strip().lower()
        updates["email_lower"] = updates["email"]
        existing = await col.find_one({"email_lower": updates["email_lower"], "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

    if "password" in updates:
        updates["password_hash"] = hash_password(updates.pop("password").strip())

    if "class_name" in updates:
        updates["class_name"] = updates["class_name"].strip().upper()
        updates["department"] = updates["class_name"]

    if "registration_number" in updates:
        reg_no = updates["registration_number"].strip().upper()
        updates["registration_number"] = reg_no
        updates["registration_number_lower"] = reg_no.lower()
        existing = await col.find_one({"registration_number_lower": reg_no.lower(), "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(status_code=400, detail="Registration number already exists")

    result = await col.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    updated = await col.find_one({"_id": oid})
    return {"success": True, "data": _serialize(updated)}


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_students_collection()

    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")

    return {"success": True, "message": "Student deleted"}


@router.get("/students/stats")
async def student_stats(current_user: dict = Depends(get_current_mongo_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    col = get_students_collection()
    total = await col.count_documents({})
    return {"success": True, "total_students": total}
