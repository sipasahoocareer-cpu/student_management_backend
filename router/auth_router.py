
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from schema.schemas import UserCreate, LoginSchema
from service.auth_service import register_student_service, login_service

router = APIRouter()


@router.post('/register-student')
def register_student(payload: UserCreate, db: Session = Depends(get_db)):
    return register_student_service(db, payload.model_dump())


@router.post('/login')
def login(payload: LoginSchema, db: Session = Depends(get_db)):
    """
    Single login endpoint for student, teacher, and admin.
    If `role` is provided in the payload it will be enforced; otherwise the
    user's stored role is used and returned.
    """
    return login_service(db, payload.email, payload.password)


