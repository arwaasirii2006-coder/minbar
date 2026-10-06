# Privacy and Security

Minbar is designed so that worshippers can follow the sermon without giving anything about themselves. This document states what is and is not collected, and which security controls exist in the code. The worshipper-facing summary is the `/privacy` page (`frontend/privacy.html`).

## Privacy

### What is not collected

| Principle | How it holds in the code |
|---|---|
| **No worshipper accounts** | `/listen` needs only a link. There is no sign-up, login or password for worshippers. |
| **No worshipper database** | The service has no database at all (`requirements.txt` contains no database driver). Room state is held in process memory (`realtime/manager.py`). |
| **No personal information** | No name, phone number, email, location or listening history is requested. A listener is represented only by an open WebSocket and a language code (`Client` in `realtime/manager.py`); IP addresses are not stored by the application. |
| **No worshipper audio** | Worshipper pages never request the microphone. Only the supervisor's broadcast page records audio. |
| **Rating stays on the device** | The "translation clarity" stars on the Sermon Ended screen are kept in page memory and are never sent to the server. |

### Data that exists briefly

| Data | Where | Lifetime |
|---|---|---|
| Sermon audio chunk or recorded file | Temporary file on the server (`services/speech_to_text.py`) | One transcription request, deleted in a `finally` block whether the request succeeds or fails |
| Sermon audio sent for transcription | OpenAI API | Processed under the operator's OpenAI account terms |
| Arabic transcript and translations | Server memory (`Room.segments`) | Until the next broadcast in that mosque, until `MINBAR_ROOM_TTL_SECONDS` (default 2 h) after the end, or until the process restarts |
| Khateeb name (optional, typed by the supervisor) | Server memory | Same as the transcript |
| Listener counts per language | Server memory | Derived live from open sockets |

### Data in the worshipper's browser

| Key | Storage | Content | Lifetime |
|---|---|---|---|
| `minbar.ui` | `localStorage` | Interface language code (`ar`/`en`/`ur`/`hi`) | Until cleared, on that device only |
| `minbar.lang` | `sessionStorage` | Sermon language code | Until the tab is closed |
| `minbar.api` | `sessionStorage` | Backend URL, only when `?api=` is used for local development | Until the tab is closed |

No cookies are set by the application, and no analytics or third-party trackers are included. The pages load fonts from Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`), which is the only third-party request a browser makes.

### Logging

Logs go to standard output only (`logger.py`); no log files are written. Transcript text is never logged. Errors are logged by type (for example `AuthenticationError`), not with request bodies.

## Secrets

- **No secrets in GitHub.** `.env` and `.env.*` (except `.env.example`) are ignored by `.gitignore` and `.dockerignore`. `git ls-files` contains no `.env`, no API key and no audio.
- **Configuration only through environment variables** (`services/config.py`), documented in [QUICKSTART.md](QUICKSTART.md#environment-variables). `.env.example` contains no real values.
- **OpenAI key** is read from `OPENAI_API_KEY` at request time and never sent to the browser. Error messages tell the operator the key is missing or invalid without echoing it.
- **Broadcast codes** come from `MINBAR_BROADCAST_CODES`. They never appear in `data/mosques.json`, in API responses or in worshipper links.
- **Screenshots** in `docs/screenshots/` were checked: the broadcast code field is masked and no key, `.env` content or personal information is visible.

## Security controls

| Area | Implementation | Code |
|---|---|---|
| Broadcast authentication | Per-mosque secret code, compared with `hmac.compare_digest`. In production a mosque with no configured code cannot broadcast (`503 codes_not_configured`). In development, a mosque with no configured code accepts any code and logs a warning. | `services/mosques.py` |
| Broadcaster token | Random 24-byte URL-safe token per start/takeover, compared in constant time. Required for audio, text, recorded uploads, stop, and broadcaster WebSockets (close `4401` otherwise). | `realtime/manager.py`, `api/common.py`, `realtime/ws.py` |
| Room creation | Only mosques in `data/mosques.json` exist; other ids get `404` / close `4404`. | `realtime/manager.py` |
| Paid AI endpoints | In production, `/transcribe`, `/transcribe_all` and `/translate` require the token of an active broadcast (`401` otherwise), so the public cannot spend the OpenAI budget. `/detect_verse` uses no AI and stays open. | `api/common.py` |
| API docs | `/docs` is disabled in production. | `main.py` |
| CORS | Explicit allow-list from `MINBAR_ALLOWED_ORIGINS`, never `*`, no credentials, methods `GET POST OPTIONS`, headers `Content-Type` and `X-Broadcaster-Token`. Production default: no cross-origin access (frontend and API share an origin). Development default: `localhost`/`127.0.0.1` on ports 8000, 8765, 5500 and 5501. | `main.py`, `services/config.py` |
| Security headers | `Content-Security-Policy` (self only, plus Google Fonts; `frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: microphone=(self), camera=(), geolocation=()`, and `Strict-Transport-Security` when the request is HTTPS. | `main.py` |
| HTTPS behind a proxy | Uvicorn runs with `--proxy-headers`, so the app sees `https`/`wss` behind Render's TLS proxy and sends HSTS. | `render.yaml`, `Dockerfile` |
| Upload limits | 25 MB per file by default (`MINBAR_MAX_UPLOAD_BYTES`), enforced while streaming the upload, before the whole body is in memory (`413`). | `services/speech_to_text.py` |
| File validation | Extension or MIME type must be an allowed audio type (`415`); fewer than 1 KB is rejected as empty (`400`). | `services/speech_to_text.py` |
| Input validation | Pydantic models with length limits (room id 40, code 80, khateeb 120, text 12,000 characters; `/live/{room}/text` 5,000). Language codes checked against an allow-list. | `api/` |
| Timeouts | OpenAI calls time out after 60 s (`MINBAR_OPENAI_TIMEOUT_SECONDS`) with 2 SDK retries. Stopping a broadcast waits at most 45 s for in-flight segments. | `services/openai_client.py`, `realtime/manager.py` |
| Concurrency guard | Only one recorded sermon can be processed per room at a time (`409 processing`). | `api/live_audio.py` |
| Safe rendering | Server text is inserted with `textContent`, never `innerHTML`. | `frontend/*.html` |
| Error responses | Uniform `{"detail": {"code", "message"}}`; unexpected errors become a generic `500` without stack traces. | `api/common.py`, `main.py` |
| Container | The Docker image runs as a non-root user (`uid 10001`). | `Dockerfile` |

## What is not implemented

Stated plainly so reviewers do not assume otherwise:

- **No request rate limiting** in the application. Protection relies on the broadcast code, broadcaster tokens, the production lock on paid endpoints, and size limits. Rate limiting can be added at the hosting layer if needed.
- **No brute-force lockout** on the broadcast code. Use a long random code.
- **No authentication for worshippers** by design; anyone with the link can read the sermon, as anyone in the mosque can hear it.
- **No encryption at rest**, because nothing is stored at rest.
