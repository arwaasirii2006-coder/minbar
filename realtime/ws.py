from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from realtime.manager import LIVE, manager
from services.config import LISTENER_LANGUAGES

log = logging.getLogger("minbar")
router = APIRouter()

# Application close codes (4000-4999) so clients know not to retry blindly.
CLOSE_UNKNOWN_ROOM = 4404
CLOSE_UNAUTHORIZED = 4401


@router.websocket("/ws/{room_id}")
async def websocket_room(
    websocket: WebSocket,
    room_id: str,
    role: str = "listener",
    language: str = "en",
    token: str | None = None,
    since: int = 0,
    session: int = 0,
):
    await websocket.accept()
    room = manager.get(room_id)
    if room is None:
        await websocket.send_json({"type": "error", "code": "unknown_room", "message": "الجامع غير موجود."})
        await websocket.close(CLOSE_UNKNOWN_ROOM)
        return

    if role not in {"listener", "broadcaster"}:
        role = "listener"
    if role == "broadcaster" and not (room.status == LIVE and room.token_ok(token)):
        await websocket.send_json({"type": "error", "code": "unauthorized", "message": "جلسة البث غير مصرح بها."})
        await websocket.close(CLOSE_UNAUTHORIZED)
        return
    if language not in LISTENER_LANGUAGES:
        await websocket.send_json({"type": "error", "code": "unsupported_language", "message": f"Unsupported language: {language}"})
        language = "en"

    client = manager.connect(room, websocket, role, language)
    try:
        await websocket.send_json({"type": "state", **room.public_state(), "language": language})
        if role == "listener" and room.segments:
            # A reconnecting client only needs what it missed in the same session.
            start = max(0, since) if session == room.session else 0
            await websocket.send_json({"type": "history", "session": room.session, "segments": manager.history(room, start)})
        await manager.counts_changed(room)

        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except ValueError:
                continue
            if not isinstance(message, dict):
                continue
            kind = message.get("type")
            if kind == "ping":
                await websocket.send_json({"type": "pong", "status": room.status})
            elif kind == "language" and role == "listener":
                new = message.get("language")
                if new in LISTENER_LANGUAGES:
                    client.language = new
                    await manager.counts_changed(room)
                else:
                    await websocket.send_json({"type": "error", "code": "unsupported_language", "message": f"Unsupported language: {new}"})
    except WebSocketDisconnect:
        pass
    except Exception:
        log.exception("websocket error")
    finally:
        manager.disconnect(room, client)
        await manager.counts_changed(room)
