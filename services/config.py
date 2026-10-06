"""Runtime configuration. Every value comes from environment variables so that
no secret ever lives in the repository. Functions (not module constants) are used
for values that tests or operators may change while the process is running."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

VERSION = "4.0.0"

TRANSLATION_LANGUAGES = ("en", "ur", "hi")
# "ar" is the reading mode for hearing-impaired worshippers: the khateeb's own words.
LISTENER_LANGUAGES = ("ar", "en", "ur", "hi")
LANGUAGE_NAMES = {"ar": "Arabic", "en": "English", "ur": "Urdu", "hi": "Hindi"}


def _env_list(name: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def is_production() -> bool:
    return os.getenv("MINBAR_ENV", "development").strip().lower() == "production"


def allowed_origins() -> list[str]:
    configured = _env_list("MINBAR_ALLOWED_ORIGINS")
    if configured:
        return configured
    # Frontend and API are served from the same origin in production, so CORS is
    # only needed for local tooling.
    return [] if is_production() else ["http://localhost:8000", "http://127.0.0.1:8000"]


def broadcast_codes() -> dict[str, str]:
    """MINBAR_BROADCAST_CODES="KHATAM-2026=secret,OTHER-ROOM=secret2"."""
    codes: dict[str, str] = {}
    for item in _env_list("MINBAR_BROADCAST_CODES"):
        room, sep, code = item.partition("=")
        if sep and room.strip() and code.strip():
            codes[room.strip().upper()] = code.strip()
    return codes


def openai_configured() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def max_upload_bytes() -> int:
    # 25 MB is also the hard limit of the OpenAI transcription endpoint.
    return _env_int("MINBAR_MAX_UPLOAD_BYTES", 25 * 1024 * 1024)


def room_ttl_seconds() -> int:
    return _env_int("MINBAR_ROOM_TTL_SECONDS", 2 * 60 * 60)


def chunk_seconds() -> int:
    return max(3, min(_env_int("MINBAR_CHUNK_SECONDS", 6), 30))


def live_flush_chunks() -> int:
    """Publish buffered words after this many chunks even without sentence punctuation."""
    return max(1, _env_int("MINBAR_LIVE_FLUSH_CHUNKS", 2))


def stt_model() -> str:
    return os.getenv("MINBAR_STT_MODEL", "whisper-1")


def translation_model() -> str:
    return os.getenv("MINBAR_TRANSLATION_MODEL", "gpt-5-mini")


def translation_reasoning_effort() -> str:
    return os.getenv("MINBAR_TRANSLATION_REASONING_EFFORT", "minimal").strip()


def openai_timeout_seconds() -> float:
    return float(_env_int("MINBAR_OPENAI_TIMEOUT_SECONDS", 60))
