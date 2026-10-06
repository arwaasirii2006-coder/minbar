"""WebSocket room behaviour and the end-to-end live flow:
broadcast start → listener → segment → Quran detection → translation → stop → ENDED."""

import asyncio

import pytest
from starlette.websockets import WebSocketDisconnect

from tests.conftest import CODE, ROOM

VERSE = "قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون"
SPEECH = "إن الحمد لله نحمده ونستعينه ونستغفره ونعوذ بالله من شرور أنفسنا."


def recv_until(ws, kind, limit=10):
    for _ in range(limit):
        m = ws.receive_json()
        if m["type"] == kind:
            return m
    raise AssertionError(f"no {kind} message")


def test_listener_receives_state(client):
    with client.websocket_connect(f"/ws/{ROOM}?language=ur") as ws:
        state = ws.receive_json()
        assert state["type"] == "state" and state["status"] == "READY" and state["language"] == "ur"


def test_unknown_room_closes(client):
    with client.websocket_connect("/ws/NOPE") as ws:
        assert ws.receive_json()["code"] == "unknown_room"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 4404


def test_broadcaster_needs_valid_token(live):
    client, token = live
    with client.websocket_connect(f"/ws/{ROOM}?role=broadcaster&token=bad") as ws:
        assert ws.receive_json()["code"] == "unauthorized"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 4401


def test_unsupported_language_falls_back(client):
    with client.websocket_connect(f"/ws/{ROOM}?language=fr") as ws:
        assert ws.receive_json()["code"] == "unsupported_language"
        assert ws.receive_json()["language"] == "en"


def test_language_counts_and_change(live):
    client, token = live
    with client.websocket_connect(f"/ws/{ROOM}?role=broadcaster&token={token}") as b:
        recv_until(b, "listeners")
        with client.websocket_connect(f"/ws/{ROOM}?language=ar") as l1, client.websocket_connect(f"/ws/{ROOM}?language=hi") as l2:
            l1.receive_json(); l2.receive_json()
            counts = recv_until(b, "listeners")
            counts = recv_until(b, "listeners") if counts["count"] < 2 else counts
            assert counts["count"] == 2 and counts["language_counts"]["ar"] == 1 and counts["language_counts"]["hi"] == 1
            l2.send_json({"type": "language", "language": "ur"})
            counts = recv_until(b, "listeners")
            assert counts["language_counts"]["hi"] == 0 and counts["language_counts"]["ur"] == 1
            l1.send_json({"type": "ping"})
            assert l1.receive_json()["type"] == "pong"
        assert client.get(f"/broadcast/{ROOM}").json()["listeners"] == 0
        assert client.get(f"/broadcast/{ROOM}").json()["status"] == "LIVE"


def test_end_to_end_live_flow_without_ai_key(client):
    """Real pipeline: segmentation, Quran detection, verified translations; the AI
    step fails cleanly because no OPENAI_API_KEY is configured in tests."""
    with client.websocket_connect(f"/ws/{ROOM}?language=en") as listener:
        assert listener.receive_json()["status"] == "READY"
        token = client.post("/broadcast/start", json={"room_id": ROOM, "code": CODE}).json()["broadcaster_token"]
        assert listener.receive_json()["type"] == "started"
        h = {"X-Broadcaster-Token": token}

        r = client.post(f"/live/{ROOM}/text", data={"arabic": VERSE + "."}, headers=h)
        assert r.json()["queued_segments"] == 1
        seg = recv_until(listener, "segment")
        assert seg["verse"]["sura"] == 3 and seg["verse"]["ayah"] == 102 and seg["verse"]["verse_only"]
        for lang in ("en", "ur", "hi"):
            assert seg["translations"][lang] == seg["verse"]["translations"][lang]
        assert seg["failed_languages"] == []

        client.post(f"/live/{ROOM}/text", data={"arabic": SPEECH}, headers=h)
        seg2 = recv_until(listener, "segment")
        assert seg2["seq"] == 2 and seg2["arabic"] == SPEECH and seg2["verse"] is None
        assert set(seg2["failed_languages"]) == {"en", "ur", "hi"}

        client.post(f"/live/{ROOM}/text", data={"arabic": "hello hello"}, headers=h)
        assert recv_until(listener, "segment")["is_unclear"] is True

        stop = client.post(f"/broadcast/{ROOM}/stop", headers=h).json()
        assert stop["verified_verses"] == 1 and stop["unclear_segments"] == 1
        ended = recv_until(listener, "ended")
        assert ended["stats"]["segments"] == 3

    replay = client.get(f"/broadcast/{ROOM}/replay").json()
    assert [s["seq"] for s in replay["segments"]] == [1, 2, 3]


def test_reconnect_history_since(live):
    client, token = live
    h = {"X-Broadcaster-Token": token}
    with client.websocket_connect(f"/ws/{ROOM}") as ws:
        state = ws.receive_json()
        client.post(f"/live/{ROOM}/text", data={"arabic": VERSE + "."}, headers=h)
        client.post(f"/live/{ROOM}/text", data={"arabic": VERSE + "."}, headers=h)
        recv_until(ws, "segment"); recv_until(ws, "segment")
    with client.websocket_connect(f"/ws/{ROOM}?since=1&session={state['session']}") as ws:
        ws.receive_json()
        assert [s["seq"] for s in ws.receive_json()["segments"]] == [2]
    with client.websocket_connect(f"/ws/{ROOM}?since=1&session=999") as ws:
        ws.receive_json()
        assert [s["seq"] for s in ws.receive_json()["segments"]] == [1, 2]


def test_live_buffer_flushes_without_punctuation(live, monkeypatch):
    client, token = live
    h = {"X-Broadcaster-Token": token}
    monkeypatch.setenv("MINBAR_LIVE_FLUSH_CHUNKS", "2")
    assert client.post(f"/live/{ROOM}/text", data={"arabic": "أيها الإخوة الكرام"}, headers=h).json()["queued_segments"] == 0
    assert client.post(f"/live/{ROOM}/text", data={"arabic": "اتقوا الله في السر والعلن"}, headers=h).json()["queued_segments"] == 1


def test_segments_publish_in_order_and_compose_verse_context(live, monkeypatch):
    """Later sentences may finish translating first; listeners still get them in order.
    Commentary around a quoted verse is AI-translated, the verse itself is verified."""
    client, token = live
    import services.pipeline as pipeline

    def fake_translate(text, lang):
        import time
        time.sleep(0.4 if "الإخوة" in text else 0.0)
        return f"<{lang}:{len(text.split())}>", []

    monkeypatch.setattr(pipeline, "translate_text", fake_translate)
    h = {"X-Broadcaster-Token": token}
    first = "أيها الإخوة الكرام تذكروا دائما قول ربنا سبحانه يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون فهذه وصية عظيمة لنا جميعا."
    with client.websocket_connect(f"/ws/{ROOM}") as ws:
        ws.receive_json()
        client.post(f"/live/{ROOM}/text", data={"arabic": first + " " + SPEECH}, headers=h)
        a, b = recv_until(ws, "segment"), recv_until(ws, "segment")
    assert (a["seq"], b["seq"]) == (1, 2)
    assert a["verse"]["ayah"] == 102 and not a["verse"]["verse_only"]
    verified = a["verse"]["translations"]["en"]
    assert a["translations"]["en"].startswith("<en:") and f"“{verified}”" in a["translations"]["en"]
    assert a["parts"]["en"]["before"] and a["parts"]["en"]["after"]
    assert b["translations"]["hi"].startswith("<hi:")
