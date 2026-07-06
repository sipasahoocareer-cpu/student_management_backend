from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Text
)

from datetime import datetime

from core.database import Base


# =========================
# USER TABLE
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, nullable=False)

    password = Column(String(255), nullable=False)

    # Role: student / teacher / admin
    role = Column(String(50), default="student")

    # Optional student details
    roll_number = Column(String(50), nullable=True)

    batch = Column(String(50), nullable=True)

    subject = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# ATTENDANCE TABLE
# =========================
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(String(20), nullable=False)

    date = Column(DateTime, default=datetime.utcnow)


# =========================
# MOCK RESULT TABLE
# =========================
class MockResult(Base):
    __tablename__ = "mock_results"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    subject = Column(String(100), nullable=False)

    marks = Column(Integer, nullable=False)

    exam_date = Column(DateTime, default=datetime.utcnow)


# =========================
# NOTES TABLE
# =========================
class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(100), nullable=False)

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# COURSE TABLE
# =========================
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(100), nullable=False)

    description = Column(Text, nullable=True)

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# COURSE COMPLETION TABLE
# =========================
class CourseCompletion(Base):
    __tablename__ = "course_completions"

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    completed_at = Column(DateTime, default=datetime.utcnow)


# =========================
# QUIZ TABLE
# =========================
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(100), nullable=False)

    description = Column(Text, nullable=True)

    total_marks = Column(Integer, nullable=False, default=100)

    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    class_name = Column(String(50), nullable=True)

    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# QUIZ QUESTION TABLE
# =========================
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)

    question = Column(Text, nullable=False)

    options = Column(Text, nullable=True)

    correct_answer = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# QUIZ SUBMISSION TABLE
# =========================
class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)

    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    answers = Column(Text, nullable=True)

    marks = Column(Integer, nullable=True)

    submitted_at = Column(DateTime, default=datetime.utcnow)


# =========================
# TEACHER RATING TABLE
# =========================
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)

    teacher_name = Column(String(100), nullable=False)

    rating = Column(Integer, nullable=False)

    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# STUDENT REQUIREMENTS TABLE
# =========================
class StudentRequirement(Base):
    __tablename__ = "student_requirements"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    requirement = Column(String(255), nullable=False)

    is_completed = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)