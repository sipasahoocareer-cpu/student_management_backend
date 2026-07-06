import os

from router.mongo_student_router import _get_fallback_admin_payload


def test_fallback_admin_payload_uses_env_or_default(monkeypatch):
    monkeypatch.delenv("ADMIN_NAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    payload = _get_fallback_admin_payload("admin", "admin123")
    assert payload is not None
    assert payload["role"] == "admin"
    assert payload["name"] == "admin"

    monkeypatch.setenv("ADMIN_NAME", "superadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret123")

    payload = _get_fallback_admin_payload("superadmin", "secret123")
    assert payload is not None
    assert payload["name"] == "superadmin"

    payload = _get_fallback_admin_payload("superadmin", "wrong")
    assert payload is None
