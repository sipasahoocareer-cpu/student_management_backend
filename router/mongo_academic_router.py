from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.binary import Binary
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from core.mongo_db import get_database, get_students_collection
from .mongo_auth import decode_token, get_current_mongo_user

router = APIRouter()


def get_notes_collection():
    return get_database()["notes"]


def get_attendance_collection():
    return get_database()["attendance"]


def get_results_collection():
    return get_database()["results"]


def serialize_doc(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("file_data", None)
    return doc


class AttendancePayload(BaseModel):
    student_id: str
    status: str
    date: str


class ResultPayload(BaseModel):
    student_id: str
    title: str
    marks: float
    total_marks: float
    remarks: Optional[str] = ""


async def get_student_or_404(student_id: str):
    try:
        oid = ObjectId(student_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student ID")

    student = await get_students_collection().find_one({"_id": oid})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.post("/notes")
async def create_note(
    title: str = Form(...),
    content: str = Form(""),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher access required")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF notes can be uploaded")

    file_bytes = await file.read()
    doc = {
        "title": title.strip(),
        "content": content.strip(),
        "filename": file.filename,
        "content_type": file.content_type,
        "file_data": Binary(file_bytes),
        "teacher_name": current_user.get("name", ""),
        "created_at": datetime.utcnow(),
    }
    result = await get_notes_collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    doc.pop("file_data", None)
    return {"success": True, "message": "Successfully uploaded", "data": doc}


@router.get("/notes")
async def list_notes(current_user: dict = Depends(get_current_mongo_user)):
    cursor = get_notes_collection().find({}).sort("created_at", -1)
    notes = [serialize_doc(doc) async for doc in cursor]
    return {"success": True, "data": notes}


@router.get("/notes/{note_id}/file")
async def get_note_file(note_id: str, token: Optional[str] = Query(None)):
    if token:
        decode_token(token)
    else:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        oid = ObjectId(note_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid note ID")

    note = await get_notes_collection().find_one({"_id": oid})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    headers = {"Content-Disposition": f'inline; filename="{note.get("filename", "note.pdf")}"'}
    return Response(content=bytes(note["file_data"]), media_type="application/pdf", headers=headers)


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    current_user: dict = Depends(get_current_mongo_user)
):
    """Delete a note (teacher or admin only)."""
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Only teachers/admin can delete notes")

    try:
        oid = ObjectId(note_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid note ID")

    result = await get_notes_collection().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    return {"success": True, "detail": "Note deleted successfully"}


@router.post("/attendance")
async def create_attendance(
    payload: AttendancePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher access required")

    student = await get_student_or_404(payload.student_id)
    doc = {
        "student_id": payload.student_id,
        "student_name": student.get("name", ""),
        "student_email": student.get("email", ""),
        "status": payload.status,
        "date": payload.date,
        "teacher_name": current_user.get("name", ""),
        "created_at": datetime.utcnow(),
    }

    await get_attendance_collection().update_one(
        {"student_id": payload.student_id, "date": payload.date},
        {"$set": doc},
        upsert=True,
    )
    return {"success": True, "message": "Attendance marked", "data": doc}


@router.get("/attendance/{student_id}")
async def list_attendance(student_id: str, current_user: dict = Depends(get_current_mongo_user)):
    if current_user.get("role") == "student" and current_user.get("sub") != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own attendance")

    cursor = get_attendance_collection().find({"student_id": student_id}).sort("date", 1)
    records = [serialize_doc(doc) async for doc in cursor]
    return {"success": True, "data": records}


@router.post("/results")
async def create_result(
    payload: ResultPayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher access required")

    student = await get_student_or_404(payload.student_id)
    doc = {
        "student_id": payload.student_id,
        "student_name": student.get("name", ""),
        "student_email": student.get("email", ""),
        "title": payload.title.strip(),
        "marks": payload.marks,
        "total_marks": payload.total_marks,
        "remarks": (payload.remarks or "").strip(),
        "teacher_name": current_user.get("name", ""),
        "created_at": datetime.utcnow(),
    }
    result = await get_results_collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return {"success": True, "message": "Result saved", "data": doc}


@router.get("/results/{student_id}")
async def list_results(student_id: str, current_user: dict = Depends(get_current_mongo_user)):
    if current_user.get("role") == "student" and current_user.get("sub") != student_id:
        raise HTTPException(status_code=403, detail="You can only view your own results")

    cursor = get_results_collection().find({"student_id": student_id}).sort("created_at", -1)
    results = [serialize_doc(doc) async for doc in cursor]
    return {"success": True, "data": results}
