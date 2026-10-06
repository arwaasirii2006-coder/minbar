# Deployment

Minbar deploys as **one web service** that serves the pages, the REST API and the WebSocket from the same URL. There is no database and no separate frontend host. The repository supports two ways to run it on Render; both use the files in this repository as they are.

| Option | Defined by | Build | Start |
|---|---|---|---|
| **A. Render Blueprint (native Python runtime)** | [`render.yaml`](../render.yaml) | `pip install -r requirements.txt` | `uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'` |
| **B. Docker** (Render Docker runtime or any container host) | [`Dockerfile`](../Dockerfile) | `docker build` (Python 3.13 slim, non-root user) | `uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips='*'` |

Note that `render.yaml` uses Render's **native Python runtime** (`runtime: python`), not Docker. Docker is the alternative when you create the service manually with the Docker runtime or deploy elsewhere.

## Option A: Render Blueprint (recommended)

`render.yaml` defines:

| Setting | Value |
|---|---|
| Service type | Web Service (`type: web`), name `minbar` |
| Runtime | `python`, `PYTHON_VERSION=3.13.5` |
| Plan | `starter` (paid; see the free-plan note below) |
| Health check | `GET /ready` |
| Instances | `numInstances: 1` — required, because room state is in memory |
| Environment | `MINBAR_ENV=production` preset; `OPENAI_API_KEY`, `MINBAR_BROADCAST_CODES`, `MINBAR_ALLOWED_ORIGINS` declared with `sync: false` (you enter the values in the dashboard; they are never in the repository) |

Steps:

1. Fork or push the repository to your GitHub account.
2. In the Render dashboard choose **New → Blueprint** and select the repository. Use the `main` branch.
3. Render reads `render.yaml` and asks for the `sync: false` values:
   - `OPENAI_API_KEY` — your OpenAI secret key.
   - `MINBAR_BROADCAST_CODES` — for example `KHATAM-2026=<long random code>`. Every mosque in `data/mosques.json` needs a code, otherwise `/ready` stays `503`.
   - `MINBAR_ALLOWED_ORIGINS` — leave empty. It is only needed if a page on another domain must call this API.
4. Apply. Render installs `requirements.txt` and starts Uvicorn on the port it assigns in `$PORT`.
5. The service becomes healthy once `GET /ready` returns `200`. In production that requires the Quran data, the translations, the mosque directory, **and** both secrets. An incomplete configuration therefore never goes live.
6. Open `https://<your-service>.onrender.com/`.

Optional variables (`MINBAR_MAX_UPLOAD_BYTES`, `MINBAR_ROOM_TTL_SECONDS`, `MINBAR_CHUNK_SECONDS`, models, timeouts, log level) can be added under **Environment**; see [QUICKSTART.md](QUICKSTART.md#environment-variables).

## Option B: Docker

```bash
docker build -t minbar .
docker run -p 10000:10000 \
  -e OPENAI_API_KEY=sk-... \
  -e MINBAR_BROADCAST_CODES="KHATAM-2026=<long random code>" \
  minbar
```

The image sets `MINBAR_ENV=production`, runs as a non-root user (uid 10001), exposes port 10000 (or `$PORT`), and has a Docker `HEALTHCHECK` on `/health` (liveness only; use `/ready` for readiness in your platform). `.dockerignore` keeps `.env`, `docs/`, audio files and local caches out of the image.

On Render with the Docker runtime: **New → Web Service**, select the repository, choose **Docker** as the runtime, set the same environment variables, set the health check path to `/ready`, and keep a single instance.

## Public URL and HTTPS

- Render provides an `https://<name>.onrender.com` URL with a managed TLS certificate. A custom domain can be added in the service settings.
- Uvicorn runs with `--proxy-headers --forwarded-allow-ips='*'` so the app sees the original `https` scheme behind Render's proxy; it then adds `Strict-Transport-Security`.
- HTTPS is **required** for the supervisor's microphone on any device other than `localhost`.
- Worshipper link for a mosque: `https://<your-domain>/listen?room=KHATAM-2026` (without `room`, the first mosque in the directory is used).

## WebSocket considerations

- Pages connect to `wss://<same host>/ws/{room}` automatically when served over HTTPS (`frontend/js/config.js`); no extra configuration is needed on Render, which supports WebSockets on web services.
- Clients send a ping every 25 seconds, which keeps connections alive through proxies with idle timeouts.
- A deploy or restart closes every socket and **clears all room state**. Listener pages reconnect automatically, but a live broadcast must be started again. Do not redeploy during a sermon.
- **Single instance only.** With more than one instance, a supervisor and a worshipper could land on different processes and never see each other.
- **Free plan:** free Render services sleep when idle and lose in-memory state. Use a paid instance for real broadcasts, or open the site a few minutes before the sermon so it is awake.

## Adding a mosque

1. Add an entry to `data/mosques.json`: `{"id": "ROOM-ID", "name": "…", "location": "…"}` and commit it.
2. Add its code to `MINBAR_BROADCAST_CODES`: `KHATAM-2026=…,ROOM-ID=…`.
3. Redeploy (outside sermon time). Worshipper link: `https://<your-domain>/listen?room=ROOM-ID`.

## Redeployment

- With auto-deploy enabled (Render's default for Blueprints), every push to `main` triggers a build and deploy.
- Manual: Render dashboard → the service → **Manual Deploy → Deploy latest commit**.
- Changing an environment variable in the dashboard also restarts the service.
- Each restart clears broadcasts and replay transcripts (in memory by design).

## Post-deployment checklist

- [ ] `GET /ready` returns `200` with `"environment": "production"`, `"openai_configured": true` and `"broadcast_codes_configured": true`
- [ ] `GET /docs` returns `404` (disabled in production)
- [ ] `/broadcast` with a wrong code shows «الرمز غير صحيح.» ("The code is incorrect.")
- [ ] A test broadcast from a phone, received on a second device on another network
- [ ] A known verse (e.g. Āl-'Imrān 3:102) appears as a gold Quran card with the QuranEnc translator
- [ ] Stopping the broadcast shows the ended screen to listeners, and replay works
- [ ] `git ls-files | grep -iE "\.env$|\.mp3|\.wav|\.m4a"` prints nothing

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Deploy never becomes healthy; `/ready` returns `503` | A required secret is missing in production | Open `/ready`: the `checks` object names the failing check. Set `OPENAI_API_KEY` and a code for every mosque in `MINBAR_BROADCAST_CODES`. |
| Login says the broadcast code is not configured | `MINBAR_BROADCAST_CODES` has no entry for that room id | Add `ROOM_ID=code` for that mosque (room ids are upper-case, from `data/mosques.json`) |
| Microphone blocked on the phone | Page opened over `http://` | Use the `https://` Render URL |
| Listeners and supervisor out of sync after scaling | More than one instance | Set instances back to 1 |
| Broadcast disappeared mid-sermon | Restart, redeploy or free-plan sleep | Keep one always-on paid instance; do not deploy during sermons |
| Audio chunks fail with "OpenAI key invalid" | Wrong or revoked key | Update `OPENAI_API_KEY` in the dashboard (this restarts the service) |

More in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
