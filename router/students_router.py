from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from service.auth_service import get_current_user, require_role
from model import User

from service.student_service import (
    get_profile_service,
    get_dashboard_service,
    get_all_students_service,
    add_student_service,
    edit_student_service,
    delete_student_service,
    create_attendance_service,
    list_attendance_service,
    create_note_service,
    list_notes_service,
    create_quiz_service,
    list_quizzes_service,
    delete_quiz_service,
    submit_quiz_service,
    mark_quiz_submission_service,
    view_quiz_results_service,
)

router = APIRouter()


@router.get('/profile')
def get_profile(user: User = Depends(get_current_user)):
    return get_profile_service(user)


@router.get('/dashboard')
def get_dashboard(user: User = Depends(get_current_user)):
    return get_dashboard_service(user)


# Admin routes

@router.get('/all', dependencies=[Depends(require_role('admin'))])
def get_all_students(db: Session = Depends(get_db)):
    return get_all_students_service(db)


@router.post('/add', dependencies=[Depends(require_role('admin'))])
def add_student(payload: dict, db: Session = Depends(get_db)):
    return add_student_service(db, payload)


@router.put('/{student_id}', dependencies=[Depends(require_role('admin'))])
def edit_student(student_id: int, payload: dict, db: Session = Depends(get_db)):
    return edit_student_service(db, student_id, payload)


@router.delete('/{student_id}', dependencies=[Depends(require_role('admin'))])
def delete_student(student_id: int, course_id: int = None, db: Session = Depends(get_db)):
    return delete_student_service(db, student_id, course_id)


# ---------- Resources: Attendance, Notes, Quiz/Marks ----------

@router.post('/attendance')
def create_attendance(user: User = Depends(require_role('teacher')), payload: dict = None, db: Session = Depends(get_db)):
    return create_attendance_service(db, user, payload or {})


@router.get('/attendance/{student_id}')
def list_attendance(student_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_attendance_service(db, student_id, user)


@router.post('/notes')
def create_note(user: User = Depends(get_current_user), payload: dict = None, db: Session = Depends(get_db)):
    return create_note_service(db, user, payload or {})


@router.get('/notes')
def list_notes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_notes_service(db, user)


@router.post('/quiz')
def create_quiz(user: User = Depends(require_role('teacher')), payload: dict = None, db: Session = Depends(get_db)):
    return create_quiz_service(db, user, payload or {})


@router.get('/quiz')
def list_quizzes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_quizzes_service(db, user)


@router.post('/quiz/{quiz_id}/delete')
def delete_quiz(quiz_id: int, user: User = Depends(require_role('teacher')), db: Session = Depends(get_db)):
    return delete_quiz_service(db, user, quiz_id)


@router.post('/quiz/{quiz_id}/submit')
def submit_quiz(quiz_id: int, user: User = Depends(get_current_user), payload: dict = None, db: Session = Depends(get_db)):
    return submit_quiz_service(db, user, quiz_id, payload or {})


@router.post('/quiz/{quiz_id}/mark')
def mark_quiz_submission(quiz_id: int, payload: dict, db: Session = Depends(get_db), user: User = Depends(require_role('teacher'))):
    return mark_quiz_submission_service(db, user, quiz_id, payload or {})


@router.get('/quiz/{quiz_id}/results')
def view_quiz_results(quiz_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return view_quiz_results_service(db, user, quiz_id)

