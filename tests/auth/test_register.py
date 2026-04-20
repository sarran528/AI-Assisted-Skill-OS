import uuid

from fastapi.testclient import TestClient


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex}@example.com"


def test_register_flow(client: TestClient) -> None:
    payload = {"email": _unique_email(), "password": "test123"}
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"].lower()
    assert data["accessToken"]


def test_register_rejects_case_duplicate(client: TestClient) -> None:
    base_email = _unique_email()
    first = {"email": base_email, "password": "test123"}
    second = {"email": base_email.upper(), "password": "test123"}

    response_first = client.post("/api/v1/auth/register", json=first)
    assert response_first.status_code == 201

    response_second = client.post("/api/v1/auth/register", json=second)
    assert response_second.status_code == 409
