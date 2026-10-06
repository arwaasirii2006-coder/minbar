"""Helpers shared by the HTTP routers. Every error response has the shape
{"detail": {"code": "...", "message": "..."}} so the frontend can show it as is."""

from __future__ import annotations

from fastapi import Header, HTTPException

from realtime.manager import LIVE, Room, manager
from services.config import TRANSLATION_LANGUAGES, is_production
from services.speech_to_text import AudioError


def api_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def audio_error(exc: AudioError) -> HTTPException:
    return api_error(exc.status, exc.code, str(exc))


def get_room(room_id: str) -> Room:
    room = manager.get(room_id)
    if room is None:
        raise api_error(404, "unknown_room", "الجامع غير موجود.")
    return room


def require_live_broadcaster(room: Room, token: str | None) -> None:
    if not room.token_ok(token):
        raise api_error(401, "unauthorized", "جلسة البث غير مصرح بها.")
    if room.status != LIVE:
        raise api_error(409, "already_ended" if room.status == "ENDED" else "not_live",
                        "انتهى البث بالفعل." if room.status == "ENDED" else "البث غير قائم.")


def require_language(lang: str) -> str:
    if lang not in TRANSLATION_LANGUAGES:
        raise api_error(400, "unsupported_language", "Supported languages are: en, ur, hi")
    return lang


def parse_languages(raw: str | None) -> list[str]:
    langs = [x.strip() for x in (raw or "").split(",") if x.strip()]
    unsupported = [x for x in langs if x not in TRANSLATION_LANGUAGES]
    if unsupported:
        raise api_error(400, "unsupported_language", f"Unsupported language: {', '.join(unsupported)}")
    return langs or list(TRANSLATION_LANGUAGES)


async def paid_api_access(x_broadcaster_token: str | None = Header(default=None)) -> None:
    """Standalone AI endpoints spend the OpenAI budget; in production only an
    active broadcaster may call them."""
    if is_production() and not manager.any_token_ok(x_broadcaster_token):
        raise api_error(401, "unauthorized", "This endpoint requires an active broadcast session.")
