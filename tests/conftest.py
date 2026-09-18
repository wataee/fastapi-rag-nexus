import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Logs in as default admin and yields Bearer auth header."""
    res = client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "admin@nexus.ai", "password": "admin123"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
