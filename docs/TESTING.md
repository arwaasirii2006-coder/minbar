# Testing

Minbar has two layers of automated tests:

1. **pytest** (`tests/test_*.py`): unit, API, realtime and integration tests. Fast, no network, no OpenAI calls.
2. **Real-browser suites** (`tests/browser/*.py`): Playwright drives Chromium/Edge against a running server, at phone (390×844) and desktop (1440×900) sizes.

Then there is a **manual evaluation** on real sermon recordings, which needs an OpenAI key and is not yet done (see the end of this page).

## Current results

Run on 6 October 2026 (Windows 11, Python 3.14.7, Microsoft Edge via Playwright 1.63), on commit `415d3de` plus this documentation change. No application code was changed by this documentation work.

| Suite | Command | Result |
|---|---|---|
| pytest | `pytest -q` | **111 passed** |
| Browser: worshipper + supervisor regression | `python tests/browser/ui_flow.py` | **39/39 passed** |
| Browser: interface languages (i18n) | `python tests/browser/i18n_flow.py` | **81/81 passed** |
| Browser: cross-origin, invalid key | `python tests/browser/cross_origin.py badkey` | **15/15 passed** |
| Browser: cross-origin, no key | `python tests/browser/cross_origin.py nokey` | **12/12 passed** |

## 1. pytest

```bash
pip install -r requirements.txt     # pytest and httpx are included
pytest -q
```

`tests/conftest.py` makes every test independent of your `.env`: it removes `OPENAI_API_KEY`, forces `MINBAR_ENV=development`, sets the broadcast code `KHATAM-2026=test-code-123`, and clears room state. Tests that need speech-to-text to succeed replace the OpenAI client with a fake. Nothing is sent to OpenAI.

| File | Tests | Area |
|---|---|---|
| `tests/test_final_api.py` | 20 | **API**: pages and static files, no hard-coded `localhost` in the frontend, security headers and CORS, `/health` and `/ready` (including production without secrets), mosques and state, code verification, already-live and takeover, stop authorization and already-ended, new session clears the previous one, TTL expiry, audio token checks, audio errors (`400`/`413`/`415`), recorded upload failure without crashing, `/translate` using the verified Quran translation with no AI, translation errors, `/transcribe` validation, paid endpoints locked in production, `/detect_verse` |
| `tests/test_cross_origin_audio.py` | 13 | **Cross-origin**: preflight from Live Server (5500) allowed in development, CORS header never a wildcard, no dev origins in production, `speech_to_text` flag in the client config, frontend targets the configured backend, `config.js` served, real browser audio formats (WebM/Opus, MP4, M4A, Ogg), three consecutive chunks through the pipeline, invalid OpenAI key returns an actionable `503` |
| `tests/test_realtime.py` | 9 | **Realtime**: state on connect, unknown room closes with `4404`, broadcaster needs a valid token (`4401`), unsupported language fallback, per-language counts and language change, end-to-end live flow without an AI key, reconnect history with `since`, buffer flush without punctuation, ordered publishing with verse context |
| `tests/test_services.py` | 9 | **Quran detection and pipeline services**: segmentation and run-on cuts, unclear/empty classification, hadith marker, normalisation map, verse context split, partial quotation inside commentary, stock phrases not reported as quotations, verse-only detection |
| `tests/test_verses.py` | 11 | **Quran detection**: Arabic normalisation (alef, tashkeel, tatweel, ya/ta marbuta), Al-Fatiha match, partial verse, too-short input, ordinary sermon text not matched, garbled verse not matched, translation lookup and errors |
| `tests/test_validate.py` | 41 | **Validation**: glossary term detection with clitics, false-positive avoidance, case handling, missing-term reporting per language |
| `tests/test_i18n.py` | 8 | **i18n**: the four dictionaries have identical keys, every key used by the pages exists, every page loads `i18n.js`, every backend error code is translated, no Arabic left in English/Hindi strings, no untranslated Arabic in static markup, interface language persisted separately from sermon language |

Run one area: `pytest tests/test_realtime.py -q`, or one test: `pytest -q -k reconnect`.

## 2. Browser tests

These scripts check what pytest cannot: real rendering, right-to-left layout, the microphone flow, WebSocket reconnects in a browser, and the interface in four languages. They print one `PASS`/`FAIL` line per check, a total, and exit with a non-zero code on failure. Screenshots for manual review are written to `tests/browser/output/` (git-ignored).

### Setup (once)

```bash
pip install -r requirements-dev.txt          # adds Playwright
python -m playwright install chromium        # or skip and use an installed Edge/Chrome, see below
```

The scripts use Playwright's bundled Chromium, and fall back to an installed Microsoft Edge. To force a browser: `MINBAR_BROWSER=msedge` or `MINBAR_BROWSER=chrome`. Chromium's simulated microphone is used, so no real microphone is needed.

### Start a test server

The suites are written for a server with an **invalid** OpenAI key, so that AI translation fails the same way every time and nothing is billed. Use port 8765 and the test code `demo-4821`:

macOS / Linux:

```bash
OPENAI_API_KEY=sk-invalid-for-tests MINBAR_ENV=development \
MINBAR_BROADCAST_CODES=KHATAM-2026=demo-4821 \
uvicorn main:app --host 127.0.0.1 --port 8765
```

Windows (PowerShell):

```powershell
$env:OPENAI_API_KEY="sk-invalid-for-tests"; $env:MINBAR_ENV="development"; $env:MINBAR_BROADCAST_CODES="KHATAM-2026=demo-4821"
uvicorn main:app --host 127.0.0.1 --port 8765
```

Variables set in the shell override `.env`, so your real key is not used. Other values can be passed with `MINBAR_TEST_BASE` and `MINBAR_TEST_CODE` (see `tests/browser/common.py`).

**Restart the server between suites.** After a suite ends its broadcast, the room stays `ENDED` for two hours, while each suite expects to begin from the waiting screen.

### Worshipper + supervisor regression (39 checks)

```bash
python tests/browser/ui_flow.py
```

Home page backgrounds and layout at 390 px, privacy page, welcome screen with the server's mosque name, waiting screen per language (including Urdu RTL), storage keys, wrong broadcast code, per-language waiting counts, microphone level test, start, five sermon cards (two Quran cards with QuranEnc attribution, hadith badge, unclear card), embedded-verse context, font size, "latest" button, Urdu and Arabic rendering, **disconnect and reconnect with the missed segment delivered once**, language change mid-sermon, end statistics, ended and replay screens, the supervisor's replay link, the microphone-denied screen, and **no JavaScript errors**.

### Interface languages (81 checks)

```bash
python tests/browser/i18n_flow.py
```

For each interface language (Arabic, English, Urdu, Hindi): switching without reload, persistence after reload, and on every screen (home, privacy, welcome, language selection, waiting, broadcast login, empty-code error, ready, broadcasting, live, both ended screens, replay, microphone denied, insecure connection) the right `dir`/`lang` and no leftover Arabic interface text; server errors shown in the interface language; sermon cards keep the sermon language's direction; no JavaScript errors. Plus one check that replay cards re-render on a language switch.

### Cross-origin (15 + 12 checks)

This reproduces the setup where pages come from a static dev server (VS Code Live Server on port 5500) and the API runs on another port. Serve the repository root on port 5500 with any static server, for example:

```bash
python -m http.server 5500 --bind 127.0.0.1
```

Then, with the test server above (invalid key) on 8765:

```bash
python tests/browser/cross_origin.py badkey
```

It checks: the actionable hint without `?api=`, mosques loaded cross-origin, assets loading, login, microphone stream, listener WebSocket across origins, start, `started` received, a real recorded chunk reaching the backend and the invalid-key message shown, **no "Failed to fetch"**, the backend answering `503` (not a network error), no request storm after a non-retryable error, stop, and `ended` received.

For the no-key variant, restart the server with `OPENAI_API_KEY=` (empty) and run `python tests/browser/cross_origin.py nokey`: the Ready screen explains the missing key, start is refused, the room stays `READY`, and three consecutive recorder chunks are each complete, independently decodable WebM files.

## 3. Testing the four languages by hand

With the server running and a valid key (see [QUICKSTART.md](QUICKSTART.md)):

1. Open `/broadcast` in one window and sign in.
2. Open `/listen` in four other windows (or private windows / phones). Choose **Arabic**, **English**, **Urdu** and **Hindi** respectively. The supervisor's Ready card shows 1 per language.
3. Start the broadcast and read, or play, a sentence containing a verse, for example «قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون».
4. Check that each window shows: Arabic → Uthmani verse text only; English → Hilali & Khan translation; Urdu → Junagarhi translation, right-to-left; Hindi → al-Omari translation. Each with its translator line.
5. Change a worshipper's language from the pill at the top of the live screen: the whole log re-renders without reconnecting, and the supervisor's counts update.
6. Switch the interface language with the globe menu: interface text changes, sermon text stays in the sermon language.

Without speaking, start the broadcast through the API and post Arabic sentences to `POST /live/KHATAM-2026/text` (form field `arabic`, header `X-Broadcaster-Token`); the commands are in [DEMO.md](DEMO.md#if-something-goes-wrong-during-the-demo).

## 4. Quran detection evaluation (one-off runs)

These figures come from evaluation runs made during development with ad-hoc scripts that are not part of the repository; the behaviour they measure is covered by `tests/test_verses.py` and `tests/test_services.py`.

| Test | Result |
|---|---|
| 150 random 7–10-word fragments of long verses, embedded between sermon sentences | 149 correct, 1 matched a different verse, 0 missed |
| 12 common sermon sentences that are not verses (including «إن الله على كل شيء قدير») | 0 false detections |
| Optimised `match_verse` compared with the original loop on 201 inputs | Identical results, about 2.4× faster |

## 5. Evaluation on real sermon recordings

**Not done yet.** Speech-to-text accuracy, AI translation quality and end-to-end latency on real sermon audio have not been measured. The tests above never call OpenAI, and no figures are claimed.

[`scripts/evaluate_sermons.py`](../scripts/evaluate_sermons.py) runs the full production path for each recording against a running server with a valid key: start, listeners in English, Urdu and Hindi, upload, transcription, verse detection, translation, stop. Recordings stay outside the repository.

```bash
python scripts/evaluate_sermons.py --code YOUR_BROADCAST_CODE "path/to/sermon-1.mp3" "path/to/sermon-2.m4a" --out path/outside/repo/results.json
```

Options: `--base` (default `http://127.0.0.1:8000`), `--room` (default `KHATAM-2026`), `--timeout` seconds per file (default 900), `--out` JSON file. For each file it reports processing time, time to the first segment, segment count, detected verses with scores, unclear segments, translation failures per language, whether every listener received the end of the broadcast, and a short sample.

Planned manual review of the results:

1. **Verses:** was every verse the khateeb recited detected, and was every detected verse actually recited? (precision and recall)
2. **Transcription:** 20 sentences per sermon compared with the audio (word errors).
3. **Translation:** a native speaker of each language reviews 10 sentences (meaning, terminology).
4. **Latency:** for a live broadcast, time from the end of a spoken sentence to its appearance on a worshipper's phone.

## Legacy file

`run_eval.py` and its output `evaluation_results.json` at the repository root are an early smoke script (one fixed sentence, an estimated cost figure). They are not part of the test suite and are superseded by the tests and the evaluation script above.
