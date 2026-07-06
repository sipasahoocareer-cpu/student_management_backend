"""
MongoDB-backed quiz router.
- POST   /api/mongo/quiz              - Teacher/Admin: create quiz (with class_name)
- GET    /api/mongo/quiz              - List quizzes (students see only their class)
- POST   /api/mongo/quiz/{id}/delete  - Teacher/Admin: delete quiz
- POST   /api/mongo/quiz/{id}/submit  - Student: submit quiz answers
- GET    /api/mongo/quiz/{id}/results - Teacher/Admin: view all submissions for a quiz
"""
from datetime import datetime
from typing import Optional

import re
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.mongo_db import get_database
from .mongo_auth import get_current_mongo_user

router = APIRouter()


def get_quizzes_collection():
    return get_database()["quizzes"]


def get_quiz_submissions_collection():
    return get_database()["quiz_submissions"]


def _serialize(doc: dict) -> dict:
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def _normalize_class_name(value: str) -> str:
    if not value:
        return ""

    value = value.strip().upper()
    if value == "PGDCA":
        return "PGDCA"

    if value.startswith("CLASS "):
        suffix = value[6:].strip()
        if suffix.isdigit():
            return f"CLASS {int(suffix)}"
        return value

    if value.isdigit():
        return f"CLASS {int(value)}"

    if value.endswith("TH") and value[:-2].isdigit():
        return f"CLASS {int(value[:-2])}"

    return value


def _class_name_query(class_name: str) -> dict:
    normalized = _normalize_class_name(class_name)
    if not normalized:
        return {"class_name": {"$exists": False}}

    if normalized == "PGDCA":
        return {"class_name": {"$regex": r"^PGDCA$", "$options": "i"}}

    match = re.match(r"^CLASS\s+(\d+)$", normalized)
    if match:
        num = match.group(1)
        pattern = rf"^(?:CLASS\s*{num}|{num}(?:TH)?)$"
        return {"class_name": {"$regex": pattern, "$options": "i"}}

    return {"class_name": {"$regex": rf"^{re.escape(normalized)}$", "$options": "i"}}


class QuizCreatePayload(BaseModel):
    title: str
    description: Optional[str] = ""
    total_marks: int = 100
    class_name: str  # e.g. "1", "2", ... "10", "PGDCA"


class QuizSubmitPayload(BaseModel):
    answers: dict  # { "0": "answer1", "1": "answer2", ... }


# ── Create Quiz ───────────────────────────────────────────────────────────────
@router.post("/quiz")
async def create_quiz(
    payload: QuizCreatePayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher or Admin access required")

    raw_class_name = payload.class_name.strip()
    normalized_class_name = _normalize_class_name(raw_class_name)
    if not normalized_class_name:
        raise HTTPException(status_code=400, detail="class_name is required")

    # teacher_id = JWT subject (email or mongo id) — used to filter quizzes per teacher
    teacher_id = current_user.get("sub") or current_user.get("email") or ""

    doc = {
        "title": payload.title.strip(),
        "description": (payload.description or "").strip(),
        "total_marks": payload.total_marks,
        "class_name": normalized_class_name,
        "class_name_raw": raw_class_name,
        "class_name_normalized": normalized_class_name,
        "teacher_name": current_user.get("name", ""),
        "teacher_id": teacher_id,
        "created_at": datetime.utcnow(),
    }

    result = await get_quizzes_collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return {"success": True, "message": "Quiz created successfully", "data": doc}


# ── List Quizzes ──────────────────────────────────────────────────────────────
@router.get("/quiz")
async def list_quizzes(
    current_user: dict = Depends(get_current_mongo_user),
):
    col = get_quizzes_collection()
    role = current_user.get("role")

    if role == "student":
        # Students only see quizzes for their own class
        student_class = _normalize_class_name(
            current_user.get("class_name") or current_user.get("department") or ""
        )
        if not student_class:
            return {"success": True, "data": []}
        query = {
            "$or": [
                _class_name_query(student_class),
                {"class_name_raw": {"$regex": rf"^{re.escape(student_class)}$", "$options": "i"}},
                {"class_name_normalized": {"$regex": rf"^{re.escape(student_class)}$", "$options": "i"}},
            ]
        }
    elif role == "teacher":
        # Teachers only see quizzes THEY created
        teacher_id = current_user.get("sub") or current_user.get("email") or ""
        teacher_name = current_user.get("name", "")
        # Match by teacher_id (new docs) OR teacher_name (legacy docs without teacher_id)
        query = {"$or": [
            {"teacher_id": teacher_id},
            {"teacher_name": teacher_name, "teacher_id": {"$exists": False}},
        ]} if teacher_id else {"teacher_name": teacher_name}
    else:
        # Admins see all quizzes
        query = {}

    cursor = col.find(query).sort("created_at", -1)
    quizzes = [_serialize(doc) async for doc in cursor]
    return {"success": True, "data": quizzes}


# ── Delete Quiz ───────────────────────────────────────────────────────────────
@router.post("/quiz/{quiz_id}/delete")
async def delete_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher or Admin access required")

    try:
        oid = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid quiz ID")

    result = await get_quizzes_collection().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Also delete all submissions for this quiz
    await get_quiz_submissions_collection().delete_many({"quiz_id": quiz_id})

    return {"success": True, "message": "Quiz deleted"}


# ── Submit Quiz ───────────────────────────────────────────────────────────────
@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: str,
    payload: QuizSubmitPayload,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required")

    try:
        oid = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid quiz ID")

    quiz = await get_quizzes_collection().find_one({"_id": oid})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Check that the student belongs to the quiz's class
    student_class = _normalize_class_name(
        current_user.get("class_name") or current_user.get("department") or ""
    )
    quiz_class = _normalize_class_name(quiz.get("class_name", ""))
    if student_class != quiz_class:
        raise HTTPException(status_code=403, detail="This quiz is not for your class")

    student_id = current_user.get("sub") or current_user.get("id", "")

    doc = {
        "quiz_id": quiz_id,
        "quiz_title": quiz.get("title", ""),
        "student_id": student_id,
        "student_name": current_user.get("name", ""),
        "answers": payload.answers,
        "marks": None,  # Will be graded by teacher
        "submitted_at": datetime.utcnow(),
    }

    result = await get_quiz_submissions_collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return {"success": True, "message": "Quiz submitted successfully", "data": doc}


# ── View Quiz Results (Teacher) ───────────────────────────────────────────────
@router.get("/quiz/{quiz_id}/results")
async def view_quiz_results(
    quiz_id: str,
    current_user: dict = Depends(get_current_mongo_user),
):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Teacher or Admin access required")

    try:
        oid = ObjectId(quiz_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid quiz ID")

    # Verify the quiz belongs to this teacher (admins can see all)
    if current_user.get("role") == "teacher":
        quiz = await get_quizzes_collection().find_one({"_id": oid})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        teacher_id = current_user.get("sub") or current_user.get("email") or ""
        teacher_name = current_user.get("name", "")
        quiz_teacher_id = quiz.get("teacher_id", "")
        quiz_teacher_name = quiz.get("teacher_name", "")
        if quiz_teacher_id and quiz_teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="This quiz does not belong to you")
        elif not quiz_teacher_id and quiz_teacher_name != teacher_name:
            raise HTTPException(status_code=403, detail="This quiz does not belong to you")

    cursor = get_quiz_submissions_collection().find({"quiz_id": quiz_id}).sort("submitted_at", -1)
    submissions = []
    async for doc in cursor:
        doc = _serialize(doc)
        submitted_at = doc.get("submitted_at")
        if hasattr(submitted_at, "isoformat"):
            submitted_at = submitted_at.isoformat()

        submissions.append({
            "id": doc.get("id"),
            "quiz_id": doc.get("quiz_id"),
            "quiz_title": doc.get("quiz_title"),
            "student_id": doc.get("student_id"),
            "student_name": doc.get("student_name"),
            "answers": doc.get("answers"),
            "marks": doc.get("marks"),
            "submitted_at": submitted_at,
            "class_name": doc.get("class_name"),
        })
    return {"success": True, "results": submissions}
