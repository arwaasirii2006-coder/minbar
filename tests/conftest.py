import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOM = "KHATAM-2026"
CODE = "test-code-123"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("MINBAR_ENV", "development")
    monkeypatch.setenv("MINBAR_BROADCAST_CODES", f"{ROOM}={CODE}")
    monkeypatch.delenv("MINBAR_MAX_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("MINBAR_ROOM_TTL_SECONDS", raising=False)
    from realtime.manager import manager
    manager.rooms.clear()
    yield
    manager.rooms.clear()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def live(client):
    """A started broadcast: returns (client, token)."""
    r = client.post("/broadcast/start", json={"room_id": ROOM, "code": CODE, "khateeb": "الشيخ"})
    assert r.status_code == 200, r.text
    return client, r.json()["broadcaster_token"]
