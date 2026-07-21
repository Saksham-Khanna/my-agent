from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["phase"] == "0-foundation"


def test_root_lists_endpoints():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "health" in body
    assert "websocket" in body
