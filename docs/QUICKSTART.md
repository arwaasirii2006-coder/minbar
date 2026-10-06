# Quick Start

From a fresh machine to a live demo broadcast in about ten minutes. Every command below matches the current repository.

## 1. Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.13** | The version used by the Dockerfile and `render.yaml`. Python 3.14 was also used during development. |
| **Git** | To clone the repository |
| **An OpenAI API key** | Needed for speech-to-text and AI translation. Without it the app still starts, but an audio broadcast cannot begin (see [Running without a key](#running-without-an-openai-key)). |
| **A modern browser** | Chrome, Edge, Safari or Firefox. The microphone works only on `localhost` or over HTTPS. |

No database, Node.js or build step is needed.

## 2. Clone

```bash
git clone https://github.com/arwaasirii2006-coder/minbar.git
cd minbar
```

## 3. Virtual environment

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows (Command Prompt): `.venv\Scripts\activate.bat`

## 4. Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, the OpenAI SDK, RapidFuzz, pytest and the other runtime packages. Browser tests need extra tooling, see [TESTING.md](TESTING.md).

## 5. Environment variables

Copy the template and edit it:

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

`.env` is read at startup by `python-dotenv` and is ignored by git. Variables already set in the shell take precedence over `.env`.

Minimum local `.env`:

```dotenv
OPENAI_API_KEY=sk-...your key...
MINBAR_ENV=development
MINBAR_BROADCAST_CODES=KHATAM-2026=choose-a-code
```

### Environment variables

All variables are read in `services/config.py` (plus `MINBAR_LOG_LEVEL` in `logger.py`). They are all listed in [`.env.example`](../.env.example).

| Name | Required | Default | Purpose | Where to obtain | Local setup | Render setup |
|---|---|---|---|---|---|---|
| `OPENAI_API_KEY` | **Yes** for audio broadcasts; required in production | *(empty)* | Speech-to-text and AI translation | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) — create a secret key in your OpenAI project with billing enabled | Put it in `.env` | Dashboard → Environment, as a secret (`sync: false` in `render.yaml`) |
| `MINBAR_ENV` | No | `development` | `production` requires the key and broadcast codes for `/ready`, disables `/docs`, locks paid AI endpoints to active broadcasters, and turns off development CORS defaults | — | `development` | Preset to `production` by `render.yaml` |
| `MINBAR_BROADCAST_CODES` | **Yes** in production | *(empty)* | Secret broadcast code per mosque: `ROOM_ID=CODE`, comma-separated, e.g. `KHATAM-2026=long-random-code`. Room ids come from `data/mosques.json` | You choose it; use a long random value | Any value. If a mosque has no code in development, any code is accepted (with a log warning) | Dashboard → Environment, as a secret |
| `MINBAR_ALLOWED_ORIGINS` | No | dev: `http://localhost` and `http://127.0.0.1` on ports 8000, 8765, 5500, 5501; production: none | Comma-separated origins allowed to call the API cross-origin. Not needed when pages are served by Minbar itself | — | Leave empty | Leave empty unless another site must call the API |
| `MINBAR_MAX_UPLOAD_BYTES` | No | `26214400` (25 MB) | Maximum audio file size; 25 MB is also OpenAI's transcription limit | — | Optional | Optional |
| `MINBAR_ROOM_TTL_SECONDS` | No | `7200` (2 h) | How long a finished sermon stays available for replay | — | Optional | Optional |
| `MINBAR_CHUNK_SECONDS` | No | `6` (clamped to 3–30) | Length of each live microphone chunk | — | Optional | Optional |
| `MINBAR_LIVE_FLUSH_CHUNKS` | No | `2` (minimum 1) | Publish buffered words after this many chunks even without sentence punctuation | — | Optional | Optional |
| `MINBAR_STT_MODEL` | No | `whisper-1` | OpenAI transcription model | OpenAI model list | Optional | Optional |
| `MINBAR_TRANSLATION_MODEL` | No | `gpt-5-mini` | OpenAI model for translating the khateeb's words | OpenAI model list | Optional | Optional |
| `MINBAR_TRANSLATION_REASONING_EFFORT` | No | `minimal` | `reasoning.effort` for `gpt-5*` / `o*` models; empty disables it | — | Optional | Optional |
| `MINBAR_OPENAI_TIMEOUT_SECONDS` | No | `60` | Timeout per OpenAI request (the SDK also retries twice) | — | Optional | Optional |
| `MINBAR_LOG_LEVEL` | No | `INFO` | Python logging level | — | Optional | Optional |
| `PORT` | Set by the platform | `10000` in Docker | Port Uvicorn listens on in the Docker and Render start commands | Provided by Render | Not used by the local command below | Provided automatically |
| `PYTHON_VERSION` | Render only | `3.13.5` | Python version for Render's native runtime | — | — | Preset in `render.yaml` |

> Never commit `.env` or paste a real key into any tracked file, issue or screenshot.

## 6. Start the backend

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check it:

```bash
curl http://127.0.0.1:8000/ready
```

You should see `"status": "ready"` and, with a key set, `"openai_configured": true`.

## 7. Frontend

There is nothing to start: FastAPI serves the pages itself.

| Page | URL |
|---|---|
| Home | http://127.0.0.1:8000/ |
| Worshipper | http://127.0.0.1:8000/listen |
| Mosque supervisor | http://127.0.0.1:8000/broadcast |
| Privacy | http://127.0.0.1:8000/privacy |
| API docs (development only) | http://127.0.0.1:8000/docs |

Optional: if you open the pages from a separate static server such as VS Code Live Server (port 5500), add the backend once per tab, e.g. `http://127.0.0.1:5500/frontend/broadcast.html?api=http://127.0.0.1:8000`.

## 8. Start a demo broadcast

1. Open http://127.0.0.1:8000/broadcast (on the computer, so `localhost` allows the microphone).
2. Mosque: **جامع الخطام** (`KHATAM-2026`). Enter the code you put in `MINBAR_BROADCAST_CODES` and press **Sign in**. The khateeb's name is optional.
3. On **Ready**, allow the microphone. The level bars move when you speak. The card shows how many worshippers are waiting, per language.
4. Press **Start broadcast** (ابدأ البث). The timer runs and detected Arabic text appears every few seconds.

Alternative: choose **Audio file** (ملف صوتي) and upload a recorded Arabic sermon (MP3, M4A, WAV, OGG, WEBM, up to 25 MB). Progress is shown while it is transcribed and translated.

The interface language of every page can be switched with the language menu at the top (العربية, English, اردو, हिन्दी).

## 9. Connect a worshipper

1. In another browser window (or a phone on the same network: `http://<computer-ip>:8000/listen` after starting Uvicorn with `--host 0.0.0.0`), open `/listen`.
2. Press **Start**, choose a sermon language (Arabic text, Urdu, English or Hindi) and continue.
3. Before the broadcast starts you see the waiting screen; once it is live, sentences appear in order. A recited verse appears as a gold Quran card with its verified translation and translator.
4. The supervisor's listener count updates immediately.

A specific mosque can be linked directly: `/listen?room=KHATAM-2026`.

## 10. Stop the broadcast

Press **Stop broadcast** (إيقاف البث) on the supervisor page. Worshippers see **The sermon has ended.** and can open **Read the sermon again**. The supervisor sees duration, peak listeners, verified verses and unclear segments, with a link to the transcript. The transcript is kept in memory for 2 hours by default.

## Running without an OpenAI key

With no key the server starts and `/ready` reports `openai_configured: false`. Pages, rooms, WebSockets, Quran detection and verified translations work, and the API (`/live/{room}/text`, `/detect_verse`) can be exercised. The supervisor page, however, **will not start an audio broadcast** and explains that `OPENAI_API_KEY` is missing, because every chunk would fail. In production `/ready` returns `503` until the key is set.

## Next steps

- Run the tests: [TESTING.md](TESTING.md)
- A two-minute demo script: [DEMO.md](DEMO.md)
- Deploy: [DEPLOYMENT.md](DEPLOYMENT.md)
- Problems: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
