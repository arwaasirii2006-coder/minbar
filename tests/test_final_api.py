"""HTTP API: pages, health, broadcast lifecycle, validation and error handling."""

import io
import time

from tests.conftest import CODE, ROOM

VERSE = "قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون"


def wav_bytes(seconds=1):
    import struct
    rate = 8000
    n = rate * seconds
    header = b"RIFF" + struct.pack("<I", 36 + n * 2) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", n * 2)
    return header + b"\x00\x00" * n


# ── pages & health ───────────────────────────────────────────────────────────

def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    r = client.get("/ready")
    assert r.status_code == 200
    checks = r.json()["checks"]
    assert checks["quran_corpus"] and checks["translations"] and checks["mosques"]


def test_ready_fails_in_production_without_secrets(client, monkeypatch):
    monkeypatch.setenv("MINBAR_ENV", "production")
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json()["checks"]["openai_configured"] is False


def test_pages_and_static(client):
    for path in ("/", "/listen", "/broadcast", "/privacy"):
        r = client.get(path)
        assert r.status_code == 200 and "text/html" in r.headers["content-type"], path
    assert client.get("/css/style.css").status_code == 200
    assert client.get("/assets/logo-full.png").status_code == 200
    assert client.get("/assets/bg-desktop.webp").status_code == 200
    r = client.get("/listen.html?room=X", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/listen?room=X"


def test_frontend_has_no_localhost_urls(client):
    for path in ("/", "/listen", "/broadcast", "/privacy"):
        assert "localhost" not in client.get(path).text


def test_security_headers_and_cors(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in r.headers
    r = client.options("/health", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") != "*"


# ── broadcast lifecycle ─────────────────────────────────────────────────────

def test_mosques_and_state(client):
    assert client.get("/broadcast/mosques").json()["mosques"][0]["id"] == ROOM
    state = client.get(f"/broadcast/{ROOM.lower()}").json()
    assert state["room_id"] == ROOM and state["status"] == "READY" and state["name"] == "جامع الخطام"
    assert client.get("/broadcast/NOPE").status_code == 404


def test_verify_code(client):
    assert client.post("/broadcast/verify", json={"room_id": ROOM, "code": "wrong"}).json()["detail"]["code"] == "invalid_code"
    assert client.post("/broadcast/verify", json={"room_id": ROOM, "code": "wrong"}).status_code == 403
    assert client.post("/broadcast/verify", json={"room_id": ROOM, "code": ""}).status_code == 400
    assert client.post("/broadcast/verify", json={"room_id": "NOPE", "code": CODE}).status_code == 404
    r = client.post("/broadcast/verify", json={"room_id": ROOM, "code": CODE})
    assert r.status_code == 200 and r.json()["config"]["chunk_seconds"] >= 3


def test_production_requires_configured_code(client, monkeypatch):
    monkeypatch.setenv("MINBAR_ENV", "production")
    monkeypatch.delenv("MINBAR_BROADCAST_CODES")
    r = client.post("/broadcast/start", json={"room_id": ROOM, "code": "anything"})
    assert r.status_code == 503 and r.json()["detail"]["code"] == "codes_not_configured"


def test_start_already_live_and_resume(live):
    client, token = live
    assert client.get(f"/broadcast/{ROOM}").json()["status"] == "LIVE"
    r = client.post("/broadcast/start", json={"room_id": ROOM, "code": CODE})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "already_live"
    resumed = client.post("/broadcast/start", json={"room_id": ROOM, "code": CODE, "resume": True}).json()
    assert resumed["broadcaster_token"] != token
    assert client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": token}).status_code == 401
    assert client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": resumed["broadcaster_token"]}).status_code == 200


def test_stop_auth_and_already_ended(live):
    client, token = live
    assert client.post(f"/broadcast/{ROOM}/stop").status_code == 401
    r = client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": token})
    assert r.status_code == 200 and r.json()["status"] == "ENDED"
    r = client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": token})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "already_ended"
    r = client.post(f"/live/{ROOM}/text", data={"arabic": VERSE}, headers={"X-Broadcaster-Token": token})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "already_ended"


def test_new_broadcast_clears_previous_session(live):
    client, token = live
    client.post(f"/live/{ROOM}/text", data={"arabic": VERSE}, headers={"X-Broadcaster-Token": token})
    client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": token})
    assert len(client.get(f"/broadcast/{ROOM}/replay").json()["segments"]) == 1
    client.post("/broadcast/start", json={"room_id": ROOM, "code": CODE})
    assert client.get(f"/broadcast/{ROOM}/replay").json()["segments"] == []


def test_ended_room_expires(live, monkeypatch):
    client, token = live
    client.post(f"/live/{ROOM}/text", data={"arabic": VERSE}, headers={"X-Broadcaster-Token": token})
    client.post(f"/broadcast/{ROOM}/stop", headers={"X-Broadcaster-Token": token})
    monkeypatch.setenv("MINBAR_ROOM_TTL_SECONDS", "1")
    time.sleep(1.1)
    state = client.get(f"/broadcast/{ROOM}").json()
    assert state["status"] == "READY" and state["segments"] == 0


# ── audio validation ────────────────────────────────────────────────────────

def test_audio_requires_live_token(client):
    files = {"file": ("a.wav", wav_bytes(), "audio/wav")}
    assert client.post(f"/live/{ROOM}/audio", files=files).status_code == 401


def test_audio_errors(live, monkeypatch):
    client, token = live
    h = {"X-Broadcaster-Token": token}
    r = client.post(f"/live/{ROOM}/audio", headers=h, files={"file": ("a.webm", b"", "audio/webm")})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "empty_audio"
    r = client.post(f"/live/{ROOM}/audio", headers=h, files={"file": ("notes.txt", b"x" * 5000, "text/plain")})
    assert r.status_code == 415 and r.json()["detail"]["code"] == "unsupported_audio"
    monkeypatch.setenv("MINBAR_MAX_UPLOAD_BYTES", "4000")
    r = client.post(f"/live/{ROOM}/audio", headers=h, files={"file": ("a.wav", wav_bytes(), "audio/wav")})
    assert r.status_code == 413 and r.json()["detail"]["code"] == "file_too_large"
    monkeypatch.delenv("MINBAR_MAX_UPLOAD_BYTES")
    # Valid audio, but no OPENAI_API_KEY: a clear 503 instead of a crash.
    r = client.post(f"/live/{ROOM}/audio", headers=h, files={"file": ("a.wav", wav_bytes(), "audio/wav")})
    assert r.status_code == 503 and r.json()["detail"]["code"] == "ai_unavailable"
    assert client.get(f"/broadcast/{ROOM}").json()["status"] == "LIVE"


def test_recorded_upload_reports_failure_without_crashing(live):
    client, token = live
    r = client.post(f"/live/{ROOM}/recorded", headers={"X-Broadcaster-Token": token}, files={"file": ("s.wav", wav_bytes(), "audio/wav")})
    assert r.status_code == 202 and r.json()["processing"]["state"] == "processing"
    for _ in range(50):
        processing = client.get(f"/broadcast/{ROOM}").json()["processing"]
        if processing["state"] != "processing":
            break
        time.sleep(0.05)
    assert processing["state"] == "failed" and "OPENAI_API_KEY" in processing["error"]
    assert processing["error_code"] == "ai_unavailable"


# ── standalone endpoints ───────────────────────────────────────────────────

def test_translate_uses_verified_quran_without_ai(client):
    r = client.post("/translate", json={"text": VERSE, "target_language": "ur"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["verse"]["sura"] == 3 and body["verse"]["ayah"] == 102
    assert body["translation"] == body["verse"]["translations"]["ur"]


def test_translate_errors(client):
    assert client.post("/translate", json={"text": VERSE, "target_language": "fr"}).json()["detail"]["code"] == "unsupported_language"
    r = client.post("/translate", json={"text": "إن الحمد لله نحمده ونستعينه ونستغفره", "target_language": "en"})
    assert r.status_code == 502 and r.json()["detail"]["code"] == "translation_failed"
    assert client.post("/translate", json={"text": "hello there", "target_language": "en"}).status_code == 400


def test_transcribe_validation(client):
    r = client.post("/transcribe", data={"target_language": "de"}, files={"file": ("a.wav", wav_bytes(), "audio/wav")})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "unsupported_language"
    r = client.post("/transcribe_all", files={"file": ("a.wav", wav_bytes(), "audio/wav")})
    assert r.status_code == 503


def test_paid_endpoints_locked_in_production(client, monkeypatch):
    monkeypatch.setenv("MINBAR_ENV", "production")
    assert client.post("/translate", json={"text": VERSE, "target_language": "en"}).status_code == 401
    assert client.post("/transcribe", files={"file": ("a.wav", io.BytesIO(wav_bytes()), "audio/wav")}).status_code == 401
    assert client.post("/detect_verse", json={"text": VERSE}).status_code == 200


def test_detect_verse(client):
    v = client.post("/detect_verse", json={"text": VERSE}).json()["verse"]
    assert (v["sura"], v["ayah"]) == (3, 102)
    assert set(v["translations"]) == {"en", "ur", "hi"}
    assert v["sources"]["en"]["source"] == "QuranEnc"
    assert client.post("/detect_verse", json={"text": "إن الحمد لله نحمده ونستعينه"}).json()["verse"] is None
