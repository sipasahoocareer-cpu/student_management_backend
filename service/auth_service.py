import os
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime

from core.crud import (
    create_user,
    authenticate_user,
    create_token_for_user,
    get_user_by_email
)

from model import User
from core.database import get_db
from core.config import settings
from .student_service import normalize_class_name

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
security = HTTPBearer()


def register_student_service(db: Session, payload: dict):

    if payload.get('password') != payload.get('confirmPassword'):
        raise HTTPException(
            status_code=400,
            detail='Passwords do not match'
        )

    email = (payload.get('email') or '').lower().strip()

    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=400,
            detail='Email already registered'
        )

    user = create_user(
        db,
        payload.get('name'),
        email,
        payload.get('password'),
        role='student',
        rollNumber=payload.get('rollNumber'),
        batch=payload.get('batch'),
        subject=payload.get('subject')
    )

    token = create_token_for_user(user)

    return {
        'success': True,
        'token': token,
        'student': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }


def login_service(db: Session, email: str, password: str):

    user = authenticate_user(
        db,
        email.lower().strip(),
        password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )

 


    token = create_token_for_user(user)

    # Return token and user info (role capitalized to match frontend options)
    return {
        'success': True,
        'token': token,
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': (user.role.value if hasattr(user.role, 'value') else user.role).capitalize()
    }


# ----------------------------
# AUTHENTICATION FUNCTIONS WITH HTTPBEARER
# ----------------------------

def _normalize_role_value(role_value):
    if role_value is None:
        return None
    if hasattr(role_value, 'value'):
        role_value = role_value.value
    role_value = str(role_value)
    if role_value.startswith('UserRole.'):
        role_value = role_value.split('.', 1)[1]
    return role_value.lower()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify JWT token from HTTPBearer and return authenticated user.
    Supports both legacy SQL tokens and Mongo auth tokens by falling back
    to email lookup and auto-creating a SQL user stub when needed.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("email")
        if email:
            email = email.lower().strip()

        sub = payload.get("sub")
        if not email and not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = None
    if email:
        user = get_user_by_email(db, email)

    if user is None and sub:
        if isinstance(sub, str) and "@" in sub:
            user = get_user_by_email(db, sub.lower().strip())
        else:
            try:
                user = db.query(User).filter(User.id == int(sub)).first()
            except (TypeError, ValueError):
                user = None

    if user is None:
        fallback_email = email
        if not fallback_email and isinstance(sub, str) and "@" not in sub:
            fallback_email = f"{sub}@mongo.local"

        if fallback_email:
            role = payload.get("role", "student")
            name = payload.get("name") or (fallback_email.split("@")[0] if fallback_email else "user")
            batch_value = normalize_class_name(payload.get("class_name") or payload.get("department") or '')
            user = create_user(
                db,
                name,
                fallback_email,
                os.urandom(32).hex(),
                role=role,
                batch=batch_value,
                subject=payload.get("subject")
            )
    else:
        if getattr(user, 'role', None) == 'student':
            class_value = normalize_class_name(payload.get("class_name") or payload.get("department") or '')
            if class_value and not getattr(user, 'batch', None):
                user.batch = class_value
                db.add(user)
                db.commit()
                db.refresh(user)

    return user

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def require_role(role):
    """
    Check if authenticated user has the required role or one of allowed roles.
    """
    def role_checker(user: User = Depends(get_current_user)):
        user_role = _normalize_role_value(getattr(user, 'role', None))
        expected_roles = [role] if not isinstance(role, (list, tuple, set)) else role
        normalized_expected = [_normalize_role_value(r) for r in expected_roles]

        if user_role not in normalized_expected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        return user

    return role_checker
