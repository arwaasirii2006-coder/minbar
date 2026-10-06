"""Regression tests for "Failed to fetch" when the frontend runs on a separate dev
server (VS Code Live Server on :5500) and the API on another port, and for the
real audio formats browsers send."""

import re
from pathlib import Path

import httpx
import pytest

from tests.conftest import CODE, ROOM
from tests.test_final_api import wav_bytes

LIVE_SERVER = "http://127.0.0.1:5500"
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def test_preflight_from_live_server_is_allowed_in_development(client):
    r = client.options(f"/live/{ROOM}/audio", headers={
        "Origin": LIVE_SERVER,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-broadcaster-token",
    })
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == LIVE_SERVER
    assert "x-broadcaster-token" in r.headers["access-control-allow-headers"].lower()


def test_cross_origin_responses_carry_cors_header_but_never_a_wildcard(client):
    r = client.post("/broadcast/verify", json={"room_id": ROOM, "code": CODE}, headers={"Origin": LIVE_SERVER})
    assert r.status_code == 200 and r.headers["access-control-allow-origin"] == LIVE_SERVER
    r = client.options("/broadcast/verify", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_production_has_no_dev_origins(monkeypatch):
    from services.config import allowed_origins
    monkeypatch.setenv("MINBAR_ENV", "production")
    assert allowed_origins() == []
    monkeypatch.setenv("MINBAR_ALLOWED_ORIGINS", "https://minbar.example")
    assert allowed_origins() == ["https://minbar.example"]


def test_config_reports_speech_to_text_availability(client, monkeypatch):
    body = client.post("/broadcast/verify", json={"room_id": ROOM, "code": CODE}).json()
    assert body["config"]["speech_to_text"] is False
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")
    body = client.post("/broadcast/verify", json={"room_id": ROOM, "code": CODE}).json()
    assert body["config"]["speech_to_text"] is True


def test_frontend_targets_configured_backend_not_page_origin():
    for page in ("index", "listen", "broadcast", "privacy"):
        html = (FRONTEND / f"{page}.html").read_text(encoding="utf-8")
        assert '<script src="js/config.js"></script>' in html, page
        assert not re.search(r'(href|src)="/(?!/)', html), f"{page}: absolute asset/page path"
        assert "location.host" not in html and "fetch('/" not in html, page
    css = (FRONTEND / "css" / "style.css").read_text(encoding="utf-8")
    assert "url('/" not in css


def test_config_js_is_served(client):
    r = client.get("/js/config.js")
    assert r.status_code == 200 and "MINBAR" in r.text


@pytest.mark.parametrize("filename,content_type", [
    ("chunk.webm", "audio/webm;codecs=opus"),   # Chrome / Edge / Firefox MediaRecorder
    ("chunk.mp4", "audio/mp4"),                 # Safari MediaRecorder
    ("chunk.ogg", "audio/ogg;codecs=opus"),
    ("Recording (10).m4a", "audio/x-m4a"),      # Windows Voice Recorder upload
    ("blob", "audio/webm"),                     # no extension, type only
])
def test_browser_audio_formats_are_accepted(filename, content_type):
    from services.speech_to_text import audio_suffix
    assert audio_suffix(filename, content_type) in {".webm", ".mp4", ".ogg", ".m4a"}


class _FakeTranscriptions:
    """Test double for the OpenAI client: records each uploaded file and returns
    the next scripted transcript. Used only in this test module."""

    def __init__(self, texts):
        self.texts = list(texts)
        self.files = []

    def create(self, model, file, language):
        data = file.read()
        self.files.append((Path(file.name).suffix, len(data), language))
        return type("R", (), {"text": self.texts.pop(0)})()


def test_consecutive_browser_chunks_flow_through_the_pipeline(live, monkeypatch):
    client, token = live
    import services.speech_to_text as stt
    fake = _FakeTranscriptions([
        "قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته",
        "ولا تموتن إلا وأنتم مسلمون.",
        "إن الحمد لله نحمده ونستعينه ونستغفره.",
    ])
    monkeypatch.setattr(stt, "get_client", lambda: type("C", (), {"audio": type("A", (), {"transcriptions": fake})()})())
    h = {"X-Broadcaster-Token": token, "Origin": LIVE_SERVER}
    with client.websocket_connect(f"/ws/{ROOM}?language=ur") as ws:
        ws.receive_json()
        results = [client.post(f"/live/{ROOM}/audio", headers=h, files={"file": ("chunk.webm", wav_bytes(), "audio/webm;codecs=opus")}) for _ in range(3)]
        assert [r.status_code for r in results] == [200, 200, 200]
        assert all(r.headers["access-control-allow-origin"] == LIVE_SERVER for r in results)
        assert [r.json()["queued_segments"] for r in results] == [0, 1, 1]
        segs = []
        while len(segs) < 2:
            m = ws.receive_json()
            if m["type"] == "segment":
                segs.append(m)
    assert [s["seq"] for s in segs] == [1, 2]
    assert (segs[0]["verse"]["sura"], segs[0]["verse"]["ayah"]) == (3, 102)
    assert segs[0]["translations"]["ur"] == segs[0]["verse"]["translations"]["ur"]
    # every chunk reached speech-to-text as its own complete file, deleted afterwards
    assert [f[0] for f in fake.files] == [".webm"] * 3 and all(f[1] > 1000 and f[2] == "ar" for f in fake.files)


def test_invalid_openai_key_returns_actionable_503(live, monkeypatch):
    client, token = live
    import openai
    import services.speech_to_text as stt

    class Rejecting:
        def create(self, **kwargs):
            raise openai.AuthenticationError("Incorrect API key", response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1/audio/transcriptions")), body=None)

    monkeypatch.setattr(stt, "get_client", lambda: type("C", (), {"audio": type("A", (), {"transcriptions": Rejecting()})()})())
    r = client.post(f"/live/{ROOM}/audio", headers={"X-Broadcaster-Token": token}, files={"file": ("chunk.webm", wav_bytes(), "audio/webm")})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "ai_key_invalid" and "OPENAI_API_KEY" in r.json()["detail"]["message"]
    assert client.get(f"/broadcast/{ROOM}").json()["status"] == "LIVE"
