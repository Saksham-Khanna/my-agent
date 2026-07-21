import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def mock_provider():
    async def mock_generate_stream(prompt):
        yield "Hello"
        yield " there"
    
    with patch("app.core.handlers.OllamaProvider") as MockProviderClass:
        provider_instance = MockProviderClass.return_value
        provider_instance.generate_stream = mock_generate_stream
        yield provider_instance

def test_websocket_chat_message(mock_provider):
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        # Initial connection message
        data = websocket.receive_json()
        assert data["type"] == "connection_status"
        
        # Initial force_sync IDLE state
        data = websocket.receive_json()
        assert data["type"] == "orb.state_changed"
        assert data["payload"]["state"] == "IDLE"
        
        # Send a chat message via task.request
        websocket.send_json({
            "type": "task.request",
            "payload": {"text": "Say hello", "mode": "talk"}
        })

        # Expect task.started
        data = websocket.receive_json()
        assert data["type"] == "task.started"
        task_id = data["payload"]["task_id"]
        assert data["payload"]["mode"] == "talk"

        # Expect THINKING
        data = websocket.receive_json()
        assert data["type"] == "orb.state_changed"
        assert data["payload"]["state"] == "THINKING"

        # Expect RESPONDING
        data = websocket.receive_json()
        assert data["type"] == "orb.state_changed"
        assert data["payload"]["state"] == "RESPONDING"

        # Expect first llm.token
        data = websocket.receive_json()
        assert data["type"] == "llm.token"
        assert data["payload"]["text"] == "Hello"

        # Expect task.progress
        data = websocket.receive_json()
        assert data["type"] == "task.progress"
        assert data["payload"]["status"] == "generating"

        # Expect second llm.token
        data = websocket.receive_json()
        assert data["type"] == "llm.token"
        assert data["payload"]["text"] == " there"
        
        # Expect second task.progress
        data = websocket.receive_json()
        assert data["type"] == "task.progress"
        assert data["payload"]["status"] == "generating"

        # Expect IDLE
        data = websocket.receive_json()
        assert data["type"] == "orb.state_changed"
        assert data["payload"]["state"] == "IDLE"

        # Expect task.completed
        data = websocket.receive_json()
        assert data["type"] == "task.completed"
        assert data["payload"]["task_id"] == task_id
