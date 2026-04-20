import uuid

from fastapi.testclient import TestClient


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex}@example.com"


def test_login_flow(client: TestClient) -> None:
    email = _unique_email()
    register_payload = {"email": email, "password": "test123"}
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_payload = {"email": email.upper(), "password": "test123"}
    login_response = client.post("/api/v1/auth/login", json=login_payload)

    assert login_response.status_code == 200
    data = login_response.json()
    assert data["accessToken"]
