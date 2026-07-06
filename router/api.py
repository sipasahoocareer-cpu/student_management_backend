from fastapi import APIRouter
from . import auth_router, students_router, course_router

router = APIRouter()
router.include_router(auth_router.router, prefix='/auth', tags=['auth'])
router.include_router(students_router.router, prefix='/students', tags=['students'])
router.include_router(course_router.router, prefix='/courses', tags=['courses'])
