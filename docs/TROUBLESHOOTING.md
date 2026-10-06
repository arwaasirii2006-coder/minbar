# Troubleshooting

Problems met during development that can still happen, each as **symptom → cause → fix**. Messages are quoted in English; the interface shows them in the selected interface language.

Quick diagnosis: open `/ready`. The `checks` object shows whether the Quran data, translations, mosque directory, OpenAI key and broadcast codes are in place.

---

## 1. Microphone permission

**Symptom.** After signing in on `/broadcast`, the page shows "Microphone permission needed" with three numbered steps, instead of the Ready screen.

**Cause.** The browser or the operating system denied microphone access to the site (on iPhone/iPad this is a per-site Safari setting).

**Fix.** Follow the three steps on screen (Settings → Safari → Microphone → Allow), then press **Try again**. On desktop, use the lock/site-settings icon in the address bar. If the microphone cannot be enabled, press **Upload a recorded sermon** to broadcast a file instead.

## 2. Microphone blocked because the page is not secure

**Symptom.** "The microphone needs a secure connection" / "The microphone only works when Minbar is opened over a secure link starting with https://".

**Cause.** Browsers expose the microphone only on `https://` pages or on `localhost`. Opening `http://192.168.x.x:8000/broadcast` from a phone is not secure.

**Fix.** Broadcast from the computer running the server (`http://127.0.0.1:8000/broadcast`), or use the deployed `https://` URL. Worshipper pages do not need the microphone and work over plain HTTP on a local network.

## 3. Backend unavailable

**Symptom.** On `/broadcast` the mosque list stays empty and the page says "Can't reach the Minbar server. Open the page from the server itself (e.g. http://127.0.0.1:8000/broadcast), or add ?api=… to the link." On `/listen` the connection indicator keeps reconnecting.

**Cause.** The FastAPI server is not running, crashed, or is on a different host/port than the page expects.

**Fix.** Start it with `uvicorn main:app --host 127.0.0.1 --port 8000` and check `http://127.0.0.1:8000/health`. Look at the terminal for a startup error (most often a missing dependency: run `pip install -r requirements.txt` inside the virtual environment).

## 4. Wrong API URL

**Symptom.** Pages load but every request fails, or they talk to an old server, after using a link with `?api=`.

**Cause.** `frontend/js/config.js` stores the `?api=` value in `sessionStorage` for the rest of the tab, so a wrong value keeps being used even after removing it from the address.

**Fix.** Open the page once with the correct value (`?api=http://127.0.0.1:8000`), or with an empty value (`?api=`) to clear it and fall back to the page's own origin, or close the tab. The value must be just the origin: `http://host:port`, without a path.

## 5. Live Server on port 5500

**Symptom.** Opening `frontend/broadcast.html` from VS Code Live Server (`http://127.0.0.1:5500/...`) shows the "Can't reach the Minbar server" message, or audio uploads failed with "Failed to fetch".

**Cause.** Live Server only serves files; the API is on another port, and the page cannot guess which. Earlier builds also lacked the CORS entries for port 5500 (fixed: development CORS now allows ports 5500 and 5501).

**Fix.** Either open the pages from FastAPI itself (`http://127.0.0.1:8000/broadcast`, recommended), or append the backend once per tab: `http://127.0.0.1:5500/frontend/broadcast.html?api=http://127.0.0.1:8000`. Keep `MINBAR_ENV=development`.

## 6. CORS

**Symptom.** The browser console shows "blocked by CORS policy"; requests from a page on another origin fail.

**Cause.** The API only accepts cross-origin requests from an explicit allow-list. In development the defaults are `http://localhost` and `http://127.0.0.1` on ports 8000, 8765, 5500 and 5501. In production there are none, because the pages are served from the same origin. Setting `MINBAR_ALLOWED_ORIGINS` **replaces** the defaults.

**Fix.** Serve the pages from Minbar itself (no CORS needed), or add the exact origin, scheme and port included, to `MINBAR_ALLOWED_ORIGINS` (comma-separated, no trailing slash) and restart.

## 7. Invalid OpenAI key

**Symptom.** The broadcast starts, but the supervisor's status line turns red: "The OpenAI key on the server is invalid or lacks permission. Update OPENAI_API_KEY, then restart the server." Recording stops. Worshippers see Arabic text with "Machine translation is unavailable for this part; the Arabic text is shown."

**Cause.** OpenAI rejected the key (`401`/`403`): mistyped, revoked, from a project without access to the model, or without billing. The server returns `503 ai_key_invalid`; the page stops sending chunks rather than repeating a request that cannot succeed.

**Fix.** Create or copy a valid key at platform.openai.com, set `OPENAI_API_KEY` in `.env` (or in the Render dashboard), restart the server and start the broadcast again. If you changed models, check `MINBAR_STT_MODEL` and `MINBAR_TRANSLATION_MODEL` are available to your project.

## 8. Missing OpenAI key

**Symptom.** On the Ready screen: "An audio broadcast can't start: speech recognition isn't configured on the server. Add OPENAI_API_KEY to the .env file, then restart the server." The Start button does nothing else. In production, `/ready` returns `503`.

**Cause.** `OPENAI_API_KEY` is empty or not set in the environment of the server process. A common variant: `.env` was edited but the server was not restarted, or `.env` is not in the directory Uvicorn was started from.

**Fix.** Put the key in `.env` at the repository root (or export it in the shell), restart Uvicorn, and confirm `"openai_configured": true` at `/ready`.

## 9. WebSocket reconnect

**Symptom.** A worshipper sees an orange "Disconnected" banner and faded cards; or the supervisor sees "The broadcast moved to another device or the session ended."

**Cause.** The worshipper's network dropped, the phone slept, or the server restarted. For the supervisor, another device took over the live broadcast (which issues a new broadcaster token), or the broadcast ended.

**Fix.** Usually none: the listener page reconnects automatically (backoff up to 15 s, immediately when the network or tab comes back) and receives only the sentences it missed, without duplicates. If the **server** restarted, the room is back to Ready and the supervisor must start the broadcast again. For a takeover, continue on the new device, or sign in again and choose to continue on this one.

## 10. Render deployment

**Symptom.** The deploy stays "unhealthy" or the URL returns `503`; or a broadcast disappears mid-sermon.

**Cause.** In production `/ready` requires `OPENAI_API_KEY` **and** a broadcast code for every mosque. Disappearing broadcasts come from restarts, redeploys, free-plan sleep, or more than one instance.

**Fix.** Open `https://<service>/ready` and fix the failing check in **Environment**. Keep exactly one instance on an always-on plan, and do not deploy during a sermon. Details: [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting).

## 11. Upload failure

**Symptom.** Choosing an audio file shows one of: "The file exceeds the size limit." (`413`), "Unsupported file format. Supported: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC." (`415`), "The audio segment is empty." (`400`), or "A recorded sermon is being processed at this mosque." (`409`). The Ready screen also refuses an oversized file before uploading it.

**Cause.** Files over `MINBAR_MAX_UPLOAD_BYTES` (25 MB, OpenAI's limit) are refused; the type is checked by extension, then by MIME type; files under 1 KB are treated as empty; only one recording per mosque is processed at a time.

**Fix.** Compress or split long recordings (for example to mono MP3 at 64 kbps, which fits about 55 minutes in 25 MB), use a supported format, or wait for the current recording to finish. Raising `MINBAR_MAX_UPLOAD_BYTES` above 25 MB does not help, because the transcription service itself refuses larger files.

## 12. Processing failure

**Symptom.** During a live broadcast: "A segment couldn't be processed; retrying…" then "…continuing with the next one." For a recorded sermon: "No clear Arabic speech was recognized in the file." or "The recorded sermon could not be processed."

**Cause.** A temporary OpenAI error or timeout (`502 audio_processing_failed`); a chunk with no usable speech; or a recording that is silent, not Arabic, or damaged.

**Fix.** Live: nothing, the page retries the chunk twice and then moves on; the broadcast stays live. If it repeats, check the server log and the network. Recorded: check the file plays and contains Arabic speech, then use **Upload another file**. Raise `MINBAR_OPENAI_TIMEOUT_SECONDS` if long files time out.

---

Still stuck? Run the test suite ([TESTING.md](TESTING.md)) to rule out an installation problem, and check the server's standard output: every failure is logged with its error type.
