from pydantic import BaseModel, EmailStr
from model.roles import UserRole

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole