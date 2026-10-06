from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.responses import JSONResponse

from api.common import api_error, audio_error, get_room, require_live_broadcaster
from realtime.manager import Room, manager
from services.segmenter import Segmenter
from services.speech_to_text import AudioError, read_upload, transcribe_audio, validate_audio
from services.text_quality import classify

log = logging.getLogger("minbar")
router = APIRouter(prefix="/live", tags=["live"])

# Pacing between recorded-sermon segments so listeners can follow along.
RECORDED_SEGMENT_DELAY = 0.35


def _not_while_processing(room: Room) -> None:
    if (room.processing or {}).get("state") == "processing":
        raise api_error(409, "processing", "جارٍ معالجة خطبة مسجلة في هذا الجامع.")


def _ingest_transcript(room: Room, text: str) -> dict:
    kind = classify(text)
    if kind == "empty":
        return {"type": "empty", "message": "لم يُلتقط كلام في هذا المقطع."}
    if kind == "unclear":
        manager.enqueue_unclear(room)
        return {"type": "unclear", "message": "مقطع غير واضح."}
    queued = manager.add_transcript(room, text)
    return {"type": "chunk", "transcript": text, "queued_segments": queued, "buffered": room.segmenter.buffer}


@router.post("/{room_id}/audio")
async def ingest_audio(
    room_id: str,
    file: UploadFile = File(...),
    x_broadcaster_token: str | None = Header(default=None),
):
    """One microphone chunk: speech-to-text now, translation/publishing in order in the background."""
    room = get_room(room_id)
    require_live_broadcaster(room, x_broadcaster_token)
    _not_while_processing(room)
    session = room.session
    try:
        data = await read_upload(file)
        arabic = await asyncio.to_thread(transcribe_audio, data, file.filename, file.content_type)
    except AudioError as exc:
        raise audio_error(exc)
    if room.session != session or room.status != "LIVE":
        return {"type": "discarded", "message": "انتهى البث قبل معالجة المقطع."}
    room.chunks_received += 1
    room.last_audio_at = time.time()
    return _ingest_transcript(room, arabic)


@router.post("/{room_id}/text")
async def ingest_text(
    room_id: str,
    arabic: str = Form(..., max_length=5000),
    x_broadcaster_token: str | None = Header(default=None),
):
    """Arabic text from an external transcriber or manual entry; same pipeline as audio after STT."""
    room = get_room(room_id)
    require_live_broadcaster(room, x_broadcaster_token)
    _not_while_processing(room)
    return _ingest_transcript(room, arabic.strip())


@router.post("/{room_id}/recorded", status_code=202)
async def ingest_recorded(
    room_id: str,
    file: UploadFile = File(...),
    x_broadcaster_token: str | None = Header(default=None),
):
    """Upload a recorded sermon. Returns immediately; progress is pushed to the
    broadcaster WebSocket and exposed in GET /broadcast/{room_id}."""
    room = get_room(room_id)
    require_live_broadcaster(room, x_broadcaster_token)
    _not_while_processing(room)
    try:
        data = await read_upload(file)
        validate_audio(data, file.filename, file.content_type)
    except AudioError as exc:
        raise audio_error(exc)

    await manager.set_processing(room, state="processing", step="transcribing", segments=0, error=None, error_code=None, filename=file.filename)
    task = asyncio.create_task(_process_recorded(room, room.session, data, file.filename, file.content_type))
    room.tasks.add(task)
    task.add_done_callback(room.tasks.discard)
    return JSONResponse({"type": "processing", "processing": room.processing}, status_code=202)


async def _process_recorded(room: Room, session: int, data: bytes, filename: str | None, content_type: str | None) -> None:
    try:
        arabic = await asyncio.to_thread(transcribe_audio, data, filename, content_type)
        del data
        if room.session != session:
            return
        if classify(arabic) != "ok":
            await manager.set_processing(room, state="failed", step="done", error_code="no_arabic_speech", error="لم يُتعرّف على كلام عربي واضح في الملف.")
            return

        segmenter = Segmenter()
        sentences = segmenter.add(arabic) + segmenter.flush()
        await manager.set_processing(room, step="translating", total=len(sentences))
        tasks = [manager.enqueue(room, s, delay=RECORDED_SEGMENT_DELAY) for s in sentences]
        for i, task in enumerate(tasks, 1):
            await asyncio.wait({task})
            if room.session != session:
                return
            await manager.set_processing(room, segments=i)
        await manager.set_processing(room, state="done", step="done")
    except AudioError as exc:
        if room.session == session:
            await manager.set_processing(room, state="failed", step="done", error_code=exc.code, error=str(exc))
    except Exception:
        log.exception("recorded sermon processing failed")
        if room.session == session:
            await manager.set_processing(room, state="failed", step="done", error_code="recorded_failed", error="تعذّرت معالجة الخطبة المسجلة.")
