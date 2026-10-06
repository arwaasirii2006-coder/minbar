"""In-memory room state. Nothing here identifies a worshipper: a listener is only
an open socket plus the language it reads. Everything is lost on restart and
replay data expires MINBAR_ROOM_TTL_SECONDS after a broadcast ends."""

from __future__ import annotations

import asyncio
import hmac
import logging
import secrets
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from services.config import LISTENER_LANGUAGES, live_flush_chunks, room_ttl_seconds
from services.mosques import get_mosque, normalize_room_id
from services.pipeline import build_segment, unclear_segment
from services.segmenter import Segmenter

log = logging.getLogger("minbar")

READY, LIVE, ENDED = "READY", "LIVE", "ENDED"
MAX_SEGMENTS = 2000
HISTORY_LIMIT = 300


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass(eq=False)
class Client:
    websocket: WebSocket
    role: str
    language: str


@dataclass
class Room:
    room_id: str
    name: str = ""
    location: str = ""
    status: str = READY
    session: int = 0
    khateeb: str = ""
    started_at: float | None = None
    ended_at: float | None = None
    broadcaster_token: str | None = None
    clients: list[Client] = field(default_factory=list)
    segments: list[dict] = field(default_factory=list)
    peak_listeners: int = 0
    unclear_segments: int = 0
    verified_verses: int = 0
    chunks_received: int = 0
    last_audio_at: float | None = None
    segmenter: Segmenter = field(default_factory=Segmenter)
    chunks_since_emit: int = 0
    processing: dict | None = None
    tail: asyncio.Task | None = None
    tasks: set = field(default_factory=set)

    @property
    def listeners(self) -> list[Client]:
        return [c for c in self.clients if c.role == "listener"]

    @property
    def broadcasters(self) -> list[Client]:
        return [c for c in self.clients if c.role == "broadcaster"]

    @property
    def language_counts(self) -> dict[str, int]:
        counts = {lang: 0 for lang in LISTENER_LANGUAGES}
        for c in self.listeners:
            counts[c.language] = counts.get(c.language, 0) + 1
        return counts

    def token_ok(self, token: str | None) -> bool:
        return bool(token and self.broadcaster_token) and hmac.compare_digest(token, self.broadcaster_token)

    def public_state(self) -> dict:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "session": self.session,
            "khateeb": self.khateeb,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "listeners": len(self.listeners),
            "language_counts": self.language_counts,
            "segments": len(self.segments),
            "processing": self.processing,
        }

    def stats(self) -> dict:
        end = self.ended_at or time.time()
        return {
            "duration_seconds": int(end - self.started_at) if self.started_at else 0,
            "peak_listeners": self.peak_listeners,
            "verified_verses": self.verified_verses,
            "unclear_segments": self.unclear_segments,
            "segments": len(self.segments),
        }


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}

    # ── rooms ────────────────────────────────────────────────────────────
    def get(self, room_id: str) -> Room | None:
        """Rooms exist only for mosques listed in data/mosques.json."""
        rid = normalize_room_id(room_id)
        mosque = get_mosque(rid)
        if mosque is None:
            return None
        room = self.rooms.get(rid)
        if room is None:
            room = self.rooms[rid] = Room(room_id=rid, name=mosque.get("name", ""), location=mosque.get("location", ""))
        self._expire(room)
        return room

    def _expire(self, room: Room) -> None:
        if room.status == ENDED and room.ended_at and time.time() - room.ended_at > room_ttl_seconds():
            room.status = READY
            room.segments.clear()
            room.khateeb = ""
            room.started_at = room.ended_at = None
            room.broadcaster_token = None
            room.processing = None

    def live_rooms(self) -> list[Room]:
        return [r for r in self.rooms.values() if r.status == LIVE]

    def any_token_ok(self, token: str | None) -> bool:
        return any(r.token_ok(token) for r in self.live_rooms())

    # ── clients ──────────────────────────────────────────────────────────
    def connect(self, room: Room, websocket: WebSocket, role: str, language: str) -> Client:
        client = Client(websocket, role, language)
        room.clients.append(client)
        room.peak_listeners = max(room.peak_listeners, len(room.listeners))
        return client

    def disconnect(self, room: Room, client: Client) -> None:
        if client in room.clients:
            room.clients.remove(client)

    async def send(self, clients: list[Client], payload: dict, room: Room) -> None:
        dead = []
        for client in list(clients):
            try:
                await client.websocket.send_json(payload)
            except Exception:
                dead.append(client)
        for client in dead:
            self.disconnect(room, client)

    async def counts_changed(self, room: Room) -> None:
        await self.send(room.broadcasters, {
            "type": "listeners",
            "count": len(room.listeners),
            "language_counts": room.language_counts,
            "peak": room.peak_listeners,
        }, room)

    # ── lifecycle ────────────────────────────────────────────────────────
    async def start(self, room: Room, khateeb: str) -> None:
        room.session += 1
        room.status = LIVE
        room.khateeb = (khateeb or "").strip()
        room.started_at = time.time()
        room.ended_at = None
        room.broadcaster_token = secrets.token_urlsafe(24)
        room.segments.clear()
        room.segmenter = Segmenter()
        room.chunks_since_emit = 0
        room.chunks_received = 0
        room.last_audio_at = None
        room.unclear_segments = room.verified_verses = 0
        room.peak_listeners = len(room.listeners)
        room.processing = None
        room.tail = None
        await self.send(room.listeners, {
            "type": "started", "room_id": room.room_id, "session": room.session, "khateeb": room.khateeb,
            "started_at": room.started_at, "ts": now_ms(),
        }, room)

    def resume(self, room: Room) -> None:
        """Hand the live session to a new device (e.g. after a page reload)."""
        room.broadcaster_token = secrets.token_urlsafe(24)

    async def end(self, room: Room) -> None:
        for text in room.segmenter.flush():
            self.enqueue(room, text)
        await self.drain(room)
        room.status = ENDED
        room.ended_at = time.time()
        payload = {"type": "ended", "room_id": room.room_id, "ts": now_ms(), "stats": room.stats()}
        await self.send(room.clients, payload, room)

    # ── segments ─────────────────────────────────────────────────────────
    def add_transcript(self, room: Room, text: str) -> int:
        """Feed live transcript text; returns how many sentences were queued."""
        sentences = room.segmenter.add(text)
        room.chunks_since_emit = 0 if sentences else room.chunks_since_emit + 1
        if not sentences and room.chunks_since_emit >= live_flush_chunks():
            sentences = room.segmenter.flush()
            room.chunks_since_emit = 0
        for sentence in sentences:
            self.enqueue(room, sentence)
        return len(sentences)

    def enqueue(self, room: Room, arabic: str, delay: float = 0.0) -> asyncio.Task:
        return self._chain(room, lambda: build_segment(arabic), delay)

    def enqueue_unclear(self, room: Room) -> asyncio.Task:
        async def build():
            return unclear_segment()
        return self._chain(room, build)

    def _chain(self, room: Room, build, delay: float = 0.0) -> asyncio.Task:
        """Build segments concurrently but publish them strictly in arrival order,
        and never into a newer broadcast session."""
        session = room.session
        previous = room.tail

        async def run():
            try:
                payload = await build()
            except Exception:
                log.exception("segment build failed")
                payload = None
            if previous is not None:
                await asyncio.wait({previous})
            if payload is not None and room.session == session and room.status == LIVE:
                if delay:
                    await asyncio.sleep(delay)
                await self.publish(room, payload)

        task = asyncio.create_task(run())
        room.tail = task
        room.tasks.add(task)
        task.add_done_callback(room.tasks.discard)
        return task

    async def publish(self, room: Room, payload: dict) -> dict:
        seq = len(room.segments) + 1
        payload = {**payload, "seq": seq, "id": f"{room.room_id}-{room.session}-{seq}", "ts": now_ms()}
        if len(room.segments) < MAX_SEGMENTS:
            room.segments.append(payload)
        if payload.get("is_unclear"):
            room.unclear_segments += 1
        if payload.get("verse"):
            room.verified_verses += 1
        await self.send(room.clients, payload, room)
        return payload

    async def drain(self, room: Room, timeout: float = 45.0) -> None:
        pending = [t for t in room.tasks if not t.done()]
        if pending:
            done, still = await asyncio.wait(pending, timeout=timeout)
            for task in still:
                task.cancel()

    async def set_processing(self, room: Room, **state) -> None:
        room.processing = {**(room.processing or {}), **state}
        await self.send(room.broadcasters, {"type": "processing", **room.processing}, room)

    def history(self, room: Room, since: int = 0) -> list[dict]:
        return [s for s in room.segments if s["seq"] > since][-HISTORY_LIMIT:]


manager = RoomManager()
