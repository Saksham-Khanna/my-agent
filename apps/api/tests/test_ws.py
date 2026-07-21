from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_websocket_sends_connection_status_on_connect():
    with client.websocket_connect("/ws") as websocket:
        message = websocket.receive_json()
        assert message["type"] == "connection_status"
        assert message["status"] == "connected"
        assert "timestamp" in message


def test_websocket_ping_pong():
    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()  # initial connection_status
        websocket.receive_json()  # initial force_sync IDLE state

        websocket.send_json({"type": "ping"})
        message = websocket.receive_json()
        assert message["type"] == "pong"
        assert "timestamp" in message
