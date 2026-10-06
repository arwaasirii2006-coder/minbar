# Project Map

A guide to every tracked file in the repository: what it is, and where to look when you want to understand or check a particular behaviour.

## Repository tree

```text
minbar/
├── main.py                     FastAPI app: pages, static files, CORS, security headers, global error handler
├── logger.py                   Logging to standard output (no log files)
├── verses.py                   Arabic normalisation, whole-sentence verse matching, QuranEnc translation lookup
├── validate.py                 Glossary detection (with Arabic clitics) and output check → glossary_warnings
│
├── api/                        HTTP endpoints
│   ├── broadcast.py            mosque list, code verification, start/resume, state, stop, replay
│   ├── live_audio.py           live audio chunks, Arabic text segments, recorded sermons (background)
│   ├── transcription.py        /transcribe, /transcribe_all
│   ├── translation.py          /translate, /detect_verse
│   ├── health.py               /health (liveness), /ready (readiness checks)
│   └── common.py               shared error format, room lookup, token and language checks, production lock
│
├── realtime/
│   ├── manager.py              in-memory rooms: READY/LIVE/ENDED, sessions, tokens, listeners and languages,
│   │                           ordered segment publishing, statistics, replay expiry
│   └── ws.py                   WebSocket protocol /ws/{room}: state, history, segments, counts, ping, language
│
├── services/
│   ├── config.py               every environment variable and its default
│   ├── mosques.py              mosque directory (data/mosques.json) and broadcast-code check
│   ├── openai_client.py        OpenAI client (timeout, retries); clear error when the key is missing
│   ├── speech_to_text.py       upload size/type validation, temporary file, Arabic transcription, error mapping
│   ├── text_quality.py         silence artefacts, empty/unclear classification, hadith label
│   ├── segmenter.py            sentence segmentation of the live transcript
│   ├── verse_service.py        verse detection (whole sentence + quotation inside commentary), context split,
│   │                           verified translations with attribution
│   ├── translator.py           AI translation of the khateeb's words with glossary hints
│   └── pipeline.py             one Arabic sentence → segment (verse, translations, failures, warnings)
│
├── frontend/                   static pages served by FastAPI (no build step)
│   ├── index.html              Home
│   ├── listen.html             Worshipper: welcome, language, waiting, live, ended, replay
│   ├── broadcast.html          Supervisor: login, ready, microphone permission, broadcasting, ended
│   ├── privacy.html            Privacy page
│   ├── js/config.js            backend URL (same origin, or ?api= for a separate dev server)
│   ├── js/i18n.js              interface language: one dictionary for ar/en/ur/hi, switcher, RTL/LTR
│   ├── css/style.css           design tokens and styles (sampled from docs/design/)
│   └── assets/                 logo, mosque/wave backgrounds, SVG icon sprite (icons and flags)
│
├── data/
│   ├── kfgqpc_hafs_v30.json    Quran text, King Fahd Complex, Hafs v30 (6,236 verses)
│   ├── translations/{en,ur,hi}.json   QuranEnc translations of the meanings of the Quran
│   ├── convert_translations.py QuranEnc CSV → JSON conversion with integrity checks
│   ├── glossary.json           10 core religious terms with approved English renderings
│   └── mosques.json            public mosque directory (demo: KHATAM-2026, جامع الخطام)
│
├── tests/
│   ├── conftest.py             isolates tests from .env (no key, test code, clean rooms)
│   ├── test_final_api.py       API, pages, security headers, broadcast lifecycle, audio errors
│   ├── test_realtime.py        WebSocket rooms, reconnect, end-to-end flow, ordering
│   ├── test_services.py        segmentation, text quality, verse detection and context
│   ├── test_verses.py          normalisation, verse matching, translation lookup
│   ├── test_validate.py        glossary checks
│   ├── test_cross_origin_audio.py  separate dev server (CORS), browser audio formats, consecutive chunks
│   ├── test_i18n.py            dictionary completeness, used keys, translated error codes
│   └── browser/                Playwright suites (ui_flow, i18n_flow, cross_origin) + shared settings
│
├── scripts/
│   └── evaluate_sermons.py     end-to-end evaluation on real recordings kept outside the repository
│
├── docs/                       documentation, design references, screenshots, scientific reference pack
│
├── requirements.txt            runtime dependencies (also pytest/httpx)
├── requirements-dev.txt        adds Playwright for the browser suites
├── .env.example                every environment variable, no real values
├── render.yaml                 Render Blueprint (native Python runtime, single instance, /ready health check)
├── Dockerfile / .dockerignore  container image (Python 3.13 slim, non-root)
├── run_eval.py, evaluation_results.json   early smoke script and its output (legacy, see TESTING.md)
└── LICENSE                     MIT
```

## Where to look

| I want to understand… | Start here | Then |
|---|---|---|
| How a spoken sentence reaches a worshipper | [ARCHITECTURE.md](ARCHITECTURE.md) | `api/live_audio.py` → `services/pipeline.py` → `realtime/manager.py` → `realtime/ws.py` |
| Where AI is used and where it is not | [AI.md](AI.md) | `services/speech_to_text.py`, `services/translator.py` |
| How Quran verses are detected | [AI.md §4](AI.md#4-quran-detection-no-ai) | `verses.py` (`match_verse`), `services/verse_service.py` (`_embedded_match`) |
| Where verse translations come from | [SOURCES.md](SOURCES.md) | `data/translations/`, `verses.get_translation` |
| What data is kept and for how long | [PRIVACY.md](PRIVACY.md) | `realtime/manager.py`, `services/speech_to_text.py` |
| Broadcast states and tokens | [ARCHITECTURE.md §3](ARCHITECTURE.md#3-session-model) | `realtime/manager.py`, `api/broadcast.py` |
| The HTTP and WebSocket contract | [API.md](API.md) | `api/`, `realtime/ws.py` |
| Interface languages and RTL/LTR | `frontend/js/i18n.js` | `tests/test_i18n.py` |
| Configuration | [QUICKSTART.md §5](QUICKSTART.md#environment-variables) | `services/config.py`, `.env.example` |
| Running it | [QUICKSTART.md](QUICKSTART.md) | [DEMO.md](DEMO.md) |
| Testing | [TESTING.md](TESTING.md) | `tests/` |
| Deploying | [DEPLOYMENT.md](DEPLOYMENT.md) | `render.yaml`, `Dockerfile` |
| Something not working | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | `GET /ready` |
| The approved screen designs | [screens.md](screens.md) | `docs/design/` |

## Documentation index

| Document | Contents |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Install, configure, run locally, first broadcast |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, request path, session model, realtime delivery |
| [AI.md](AI.md) | AI methodology, Quran detection, glossary, failure behaviour, limitations |
| [SOURCES.md](SOURCES.md) | Quran text, translations, glossary: origin and verification |
| [PRIVACY.md](PRIVACY.md) | What is and is not collected, browser storage, security controls |
| [API.md](API.md) | Data files, HTTP endpoints, WebSocket messages |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Render Blueprint, Docker, HTTPS/WebSocket notes, live demo |
| [TESTING.md](TESTING.md) | pytest, browser suites, results, real-sermon evaluation method |
| [DEMO.md](DEMO.md) | Two-minute demo script and recovery steps |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Symptom → cause → fix |
| [screens.md](screens.md) | Screen specification (Arabic) |
| [screenshots/](screenshots/) | Screenshots of the current interface |
