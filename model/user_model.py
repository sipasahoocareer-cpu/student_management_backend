from sqlalchemy import Column, Integer, String, Enum
from core.database import Base
from model.roles import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password = Column(String, nullable=False)

    role = Column(
        Enum(UserRole),
        default=UserRole.STUDENT
    )