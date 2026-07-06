from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from dependecy.role import role_required
from core.database import get_db
from model import User
from core.crud import create_user
from sqlalchemy.orm import Session
from fastapi import HTTPException

router = APIRouter()


@router.get("/admin-dashboard")
def admin_dashboard(
    user = Depends(role_required(["admin"])),
    db: Session = Depends(get_db)
):

    total_students = db.query(User).filter(User.role == 'student').count()

    return {
        "message": "Welcome Admin",
        "total_students": int(total_students),
        "user": user
    }



@router.get('/teachers', dependencies=[Depends(role_required(["admin"]))])
def list_teachers(db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.role == 'teacher').all()
    data = [{ 'id': t.id, 'name': t.name, 'email': t.email, 'subject': getattr(t, 'subject', None) } for t in teachers]
    return { 'success': True, 'data': data }


@router.post('/teachers', dependencies=[Depends(role_required(["admin"]))])
def create_teacher(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get('email') or '').lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')

    user = create_user(
        db=db,
        name=payload.get('name'),
        email=email,
        password=payload.get('password') or 'password',
        role='teacher',
        subject=payload.get('subject')
    )

    return { 'success': True, 'data': { 'id': user.id, 'name': user.name, 'email': user.email } }


@router.put('/teachers/{teacher_id}', dependencies=[Depends(role_required(["admin"]))])
def edit_teacher(teacher_id: int, payload: dict, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == 'teacher').first()
    if not teacher:
        raise HTTPException(status_code=404, detail='Teacher not found')

    for key in ['name', 'email', 'subject']:
        if key in payload:
            if key == 'email':
                setattr(teacher, 'email', (payload[key] or '').lower().strip())
            else:
                setattr(teacher, key, payload[key])

    if 'password' in payload and payload.get('password'):
        teacher.password = create_user.__globals__['get_password_hash'](payload.get('password'))

    db.commit()
    db.refresh(teacher)

    return { 'success': True, 'data': { 'id': teacher.id, 'name': teacher.name } }


@router.delete('/teachers/{teacher_id}', dependencies=[Depends(role_required(["admin"]))])
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == 'teacher').first()
    if not teacher:
        raise HTTPException(status_code=404, detail='Teacher not found')

    db.delete(teacher)
    db.commit()

    return { 'success': True }