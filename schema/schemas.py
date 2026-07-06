from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    confirmPassword: str
    rollNumber: Optional[str] = None
    batch: Optional[str] = None
    subject: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginSchema(BaseModel):
    email: EmailStr
    password: str



class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None


class QuizQuestionCreate(BaseModel):
    question: str
    options: Optional[str] = None
    correct_answer: Optional[str] = None


class QuizEngineCreate(BaseModel):
    title: str
    description: Optional[str] = None
    total_marks: Optional[int] = 100
    class_name: str
    questions: Optional[List[QuizQuestionCreate]] = []


class QuizSubmit(BaseModel):
    answers: Optional[str] = None


class QuizMark(BaseModel):
    student_id: int
    marks: int


class CourseOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    teacher_id: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionOut(BaseModel):
    id: int
    question: str
    options: Optional[str] = None
    correct_answer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizEngineOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    total_marks: int
    course_id: Optional[int] = None
    teacher_id: int
    class_name: Optional[str] = None
    questions: Optional[List[QuizQuestionOut]] = []
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizSubmissionOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    answers: Optional[str] = None
    marks: Optional[int] = None
    submitted_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class QuizEngineResultsOut(BaseModel):
    quiz: QuizEngineOut
    results: List[QuizSubmissionOut]

    model_config = ConfigDict(from_attributes=True)


class CourseCompletionCreate(BaseModel):
    student_id: int


class CourseCompletionOut(BaseModel):
    id: int
    course_id: int
    student_id: int
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StudentRequirementBase(BaseModel):
    student_id: int
    requirement: str
    is_completed: bool = False
    notes: Optional[str] = None


class StudentRequirementCreate(StudentRequirementBase):
    pass


class StudentRequirementOut(StudentRequirementBase):
    id: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
