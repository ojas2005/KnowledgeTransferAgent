from app.auth import authenticate, create_session


def test_invalid_user_cannot_authenticate():
    assert authenticate("missing", "password") is None


def test_valid_demo_user_authenticates():
    assert authenticate("ada", "demo-password")["id"] == 1


def test_session_contains_user_id(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    assert create_session(1).startswith("1.")
