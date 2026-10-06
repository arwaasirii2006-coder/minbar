# Minbar — Architecture

## Runtime

One FastAPI process serves the static frontend, the REST API and the WebSocket on the same origin. Room state is in memory (single instance by design: no worshipper data is ever persisted).

```text
Supervisor browser (broadcast.html)
  MediaRecorder restarted every MINBAR_CHUNK_SECONDS  → complete audio file per chunk
  or recorded sermon upload
        │ POST /live/{room}/audio | /recorded   (X-Broadcaster-Token)
        ▼
  api/live_audio.py
        │ read_upload (size cap) → validate_audio (type, empty)
        ▼
  services/speech_to_text.py  — temp file → OpenAI STT (ar) → delete
        ▼
  services/text_quality.py    — silence artefacts → empty; non-Arabic → unclear
        ▼
  realtime/manager.py         — per-room Segmenter (sentence or flush after N chunks)
        │ enqueue(): build concurrently, publish strictly in order, same session only
        ▼
  services/pipeline.py
        ├─ services/verse_service.py → verses.match_verse (whole sentence)
        │                            → shingle index (partial quote inside commentary)
        │      verified translation from data/translations/*.json (QuranEnc)
        └─ services/translator.py    → OpenAI (gpt-5-mini) + glossary hint + check_glossary
        ▼
  RoomManager.publish → WebSocket /ws/{room} → listeners (ar/en/ur/hi) + broadcaster
```

## Room model

| Field | Meaning |
|---|---|
| `status` | `READY` → `LIVE` → `ENDED` (expires back to `READY` after `MINBAR_ROOM_TTL_SECONDS`) |
| `session` | increments on each start; late work from an older session is discarded |
| `broadcaster_token` | random per start/resume; required for audio, text, recorded and stop |
| `clients` | WebSocket + role (`listener`/`broadcaster`) + language. No identity |
| `language_counts` | derived from connected listeners; pushed to broadcasters on every change |
| `segments` | ordered `seq` list of the current session (replay + reconnect history) |
| `processing` | recorded-sermon progress: `processing/done/failed`, step, counts |

Rooms exist only for mosques listed in `data/mosques.json`; unknown room ids get 404 / WS close 4404, so clients cannot create rooms.

## Ordering and failure isolation

- Each sentence becomes an asyncio task chained to the previous one: translation runs in parallel, publication waits for the predecessor → listeners always see sermon order.
- Translation runs per language; a failure marks that language in `failed_languages` and keeps the Arabic text and any verified verse translation.
- STT failures return 502/503 for that chunk only; the broadcast stays `LIVE` and the supervisor page retries transient failures then continues with the next chunk.
- A global exception handler turns unexpected errors into a JSON 500 without stopping the process.

## Security

- Broadcast codes come from `MINBAR_BROADCAST_CODES` (constant-time comparison); the public room id never reveals the code.
- CORS is an explicit allow-list (none needed in production because of same-origin).
- CSP, `nosniff`, `Referrer-Policy`, `Permissions-Policy: microphone=(self)`, HSTS behind HTTPS.
- In production the paid AI endpoints require an active broadcaster token.
- Frontend renders all server text with `textContent` (no HTML injection).

## Limitation

Live audio is sent as short complete files (MediaRecorder restart) rather than a streaming ASR socket. The listener contract (`segment` messages) does not depend on this, so a streaming ASR provider can replace `speech_to_text.py` later.
