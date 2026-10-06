"""Mosque directory (public, in data/mosques.json) and broadcast-code checks
(secret, from MINBAR_BROADCAST_CODES). The room id is public because it is part
of the worshipper link; the broadcast code never leaves the server."""

from __future__ import annotations

import hmac
import json
import logging
from functools import lru_cache
from pathlib import Path

from services.config import broadcast_codes, is_production

log = logging.getLogger("minbar")

_FILE = Path(__file__).resolve().parents[1] / "data" / "mosques.json"


class BroadcastAuthError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def normalize_room_id(room_id: str) -> str:
    return (room_id or "").strip().upper()


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    with open(_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return {normalize_room_id(m["id"]): m for m in data["mosques"]}


def list_mosques() -> list[dict]:
    return [{"id": rid, "name": m.get("name", ""), "location": m.get("location", "")} for rid, m in _load().items()]


def get_mosque(room_id: str) -> dict | None:
    return _load().get(normalize_room_id(room_id))


def check_broadcast_code(room_id: str, code: str) -> None:
    rid = normalize_room_id(room_id)
    if get_mosque(rid) is None:
        raise BroadcastAuthError(404, "unknown_mosque", "الجامع غير موجود.")
    code = (code or "").strip()
    if not code:
        raise BroadcastAuthError(400, "missing_code", "أدخل رمز البث.")

    expected = broadcast_codes().get(rid)
    if expected is None:
        if is_production():
            raise BroadcastAuthError(503, "codes_not_configured", "رمز البث غير مُعدّ لهذا الجامع.")
        log.warning("MINBAR_BROADCAST_CODES has no code for %s; accepting any code (development only).", rid)
        return
    if not hmac.compare_digest(code.encode(), expected.encode()):
        raise BroadcastAuthError(403, "invalid_code", "الرمز غير صحيح.")
