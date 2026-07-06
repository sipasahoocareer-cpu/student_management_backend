from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
import os

DB_PATH = os.environ.get(
    'DATABASE_URL',
    'sqlite:///./student_management.db'
)

engine_kwargs = {}
if DB_PATH.startswith('sqlite'):
    engine_kwargs['connect_args'] = {"check_same_thread": False}

engine = create_engine(
    DB_PATH,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():
    db_file = Path('./student_management.db')

    if not db_file.parent.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)

    from model import (
        User,
        Attendance,
        MockResult,
        Note,
        Rating,
        StudentRequirement
    )

    Base.metadata.create_all(bind=engine)
    _ensure_quiz_class_name_column()


def _ensure_quiz_class_name_column():
    inspector = inspect(engine)
    if inspector.has_table('quizzes'):
        columns = [col['name'] for col in inspector.get_columns('quizzes')]
        if 'class_name' not in columns:
            try:
                with engine.begin() as conn:
                    conn.execute(text('ALTER TABLE quizzes ADD COLUMN class_name VARCHAR(50)'))
            except Exception:
                pass


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()