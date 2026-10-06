from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from api.common import api_error, get_room
from realtime.manager import ENDED, LIVE, manager
from services.config import chunk_seconds, max_upload_bytes
from services.mosques import BroadcastAuthError, check_broadcast_code, list_mosques

router = APIRouter(prefix="/broadcast", tags=["broadcast"])


class CodeRequest(BaseModel):
    room_id: str = Field(min_length=1, max_length=40)
    code: str = Field(default="", max_length=80)


class StartRequest(CodeRequest):
    khateeb: str = Field(default="", max_length=120)
    resume: bool = False


def _check_code(room_id: str, code: str) -> None:
    try:
        check_broadcast_code(room_id, code)
    except BroadcastAuthError as exc:
        raise api_error(exc.status, exc.code, exc.message)


def _client_config() -> dict:
    return {"chunk_seconds": chunk_seconds(), "max_upload_bytes": max_upload_bytes()}


@router.get("/mosques")
async def mosques():
    return {"mosques": list_mosques()}


@router.post("/verify")
async def verify(request: CodeRequest):
    _check_code(request.room_id, request.code)
    room = get_room(request.room_id)
    return {"valid": True, "room": room.public_state(), "config": _client_config()}


@router.post("/start")
async def start(request: StartRequest):
    _check_code(request.room_id, request.code)
    room = get_room(request.room_id)
    if room.status == LIVE:
        if not request.resume:
            raise api_error(409, "already_live", "البث قائم بالفعل في هذا الجامع.")
        manager.resume(room)
    else:
        await manager.start(room, request.khateeb)
    return {
        **room.public_state(),
        "broadcaster_token": room.broadcaster_token,
        "config": _client_config(),
    }


@router.get("/{room_id}")
async def state(room_id: str):
    return get_room(room_id).public_state()


@router.post("/{room_id}/stop")
async def stop(room_id: str, x_broadcaster_token: str | None = Header(default=None)):
    room = get_room(room_id)
    if not room.token_ok(x_broadcaster_token):
        raise api_error(401, "unauthorized", "جلسة البث غير مصرح بها.")
    if room.status == ENDED:
        raise api_error(409, "already_ended", "انتهى البث بالفعل.")
    if room.status != LIVE:
        raise api_error(409, "not_live", "البث غير قائم.")
    await manager.end(room)
    return {"room_id": room.room_id, "status": room.status, **room.stats()}


@router.get("/{room_id}/replay")
async def replay(room_id: str):
    room = get_room(room_id)
    return {
        "room_id": room.room_id,
        "name": room.name,
        "status": room.status,
        "khateeb": room.khateeb,
        "started_at": room.started_at,
        "segments": room.segments,
    }
