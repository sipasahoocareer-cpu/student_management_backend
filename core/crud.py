from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta
from core.config import settings
from utils.hash_util import hash_password, verify_password as verify_hashed_password

from model import (
    User,
    Attendance,
    MockResult,
    Note,
    Rating,
    StudentRequirement
)
from model.roles import UserRole

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return verify_hashed_password(plain_password, hashed_password)


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(
        User.email == email
    ).first()


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role: str = 'student',
    rollNumber: str = None,
    batch: str = None,
    subject: str = None
):

    hashed_password = get_password_hash(password)
    
    # Normalize role to plain string values for consistent comparisons
    if isinstance(role, str):
        role_value = UserRole[role.upper()].value
    else:
        role_value = role.value if hasattr(role, 'value') else str(role)

    user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role_value,
        roll_number=rollNumber,
        batch=batch,
        subject=subject,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str
):

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user


def create_token_for_user(user):
    

    payload = {
        "sub": user.email,
        'role':user.role,
        "exp": datetime.now() + timedelta(hours=1)
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token
