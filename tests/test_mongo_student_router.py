import pytest
from fastapi.testclient import TestClient

from main import app
from router.mongo_auth import create_token
import router.mongo_student_router as mongo_student_router
from utils.hash_util import hash_password


@pytest.fixture
def client():
    return TestClient(app)


def test_add_student_returns_503_when_database_is_unavailable(monkeypatch, client):
    monkeypatch.setattr(mongo_student_router, "get_students_collection", lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    token = create_token({"sub": "admin", "role": "admin", "name": "admin", "email": ""})
    response = client.post(
        "/api/mongo/students",
        json={"name": "Test Student", "password": "1234", "class_name": "1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503
    assert "Database" in response.json()["detail"]


def test_student_login_accepts_name_identifier_without_lowercase_fields(monkeypatch, client):
    class FakeCursor:
        def __init__(self, docs):
            self._docs = list(docs)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._docs:
                raise StopAsyncIteration
            return self._docs.pop(0)

    class FakeCollection:
        def __init__(self, docs):
            self._docs = docs

        async def find_one(self, query):
            return None

        def find(self, query):
            return FakeCursor(self._docs)

    student_doc = {
        "_id": "student-1",
        "name": "Alex Rivera",
        "email": "alex@example.com",
        "registration_number": "REG-001",
        "password_hash": hash_password("student123"),
    }

    monkeypatch.setattr(mongo_student_router, "get_admins_collection", lambda: FakeCollection([]))
    monkeypatch.setattr(mongo_student_router, "get_teachers_collection", lambda: FakeCollection([]))
    monkeypatch.setattr(mongo_student_router, "get_students_collection", lambda: FakeCollection([student_doc]))

    response = client.post(
        "/api/mongo/auth/login",
        json={"identifier": "Alex Rivera", "password": "student123"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert response.json()["name"] == "Alex Rivera"
