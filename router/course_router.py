from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from schema.schemas import (
    CourseCreate,
    CourseCompletionCreate,
    CourseCompletionOut,
    CourseOut,
    QuizEngineCreate,
    QuizEngineOut,
    QuizEngineResultsOut,
    QuizSubmissionOut,
    QuizSubmit,
    QuizMark,
)
from service.auth_service import get_current_user, require_role
from service.student_service import (
    create_course_service,
    list_courses_service,
    list_course_quizzes_service,
    create_quiz_engine_service,
    get_quiz_engine_service,
    submit_quiz_engine_service,
    mark_quiz_engine_submission_service,
    mark_course_complete_service,
    view_quiz_engine_results_service,
)

router = APIRouter()


@router.post('', response_model=CourseOut)
def create_course(payload: CourseCreate, user = Depends(require_role(['teacher', 'admin'])), db: Session = Depends(get_db)):
    return create_course_service(db, user, payload.model_dump())


@router.get('', response_model=List[CourseOut])
def list_courses(user = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_courses_service(db, user)


@router.post('/{course_id}/quiz-engine', response_model=QuizEngineOut)
def create_quiz_engine(course_id: int, payload: QuizEngineCreate, user = Depends(require_role(['teacher'])), db: Session = Depends(get_db)):
    payload_data = payload.model_dump()
    payload_data['course_id'] = course_id
    return create_quiz_engine_service(db, user, payload_data)


@router.get('/{course_id}/quizzes', response_model=List[QuizEngineOut])
def list_course_quizzes(course_id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_course_quizzes_service(db, course_id, user)


@router.post('/{course_id}/complete', response_model=CourseCompletionOut)
def complete_course(course_id: int, payload: CourseCompletionCreate, user = Depends(require_role(['teacher', 'admin'])), db: Session = Depends(get_db)):
    return mark_course_complete_service(db, user, course_id, payload.model_dump())


@router.get('/quiz-engine/{quiz_id}', response_model=QuizEngineOut)
def get_quiz_engine(quiz_id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_quiz_engine_service(db, user, quiz_id)


@router.post('/quiz-engine/{quiz_id}/submit', response_model=QuizSubmissionOut)
def submit_quiz_engine(quiz_id: int, payload: QuizSubmit, user = Depends(get_current_user), db: Session = Depends(get_db)):
    return submit_quiz_engine_service(db, user, quiz_id, payload.model_dump())


@router.post('/quiz-engine/{quiz_id}/mark', response_model=QuizSubmissionOut)
def mark_quiz_engine_submission(quiz_id: int, payload: QuizMark, user = Depends(require_role(['teacher'])), db: Session = Depends(get_db)):
    return mark_quiz_engine_submission_service(db, user, quiz_id, payload.model_dump())


@router.get('/quiz-engine/{quiz_id}/results', response_model=QuizEngineResultsOut)
def view_quiz_engine_results(quiz_id: int, user = Depends(get_current_user), db: Session = Depends(get_db)):
    return view_quiz_engine_results_service(db, user, quiz_id)
