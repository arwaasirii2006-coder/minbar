# Final Release Checklist

Status as of the "Integrate Minbar final production release" commit. ✅ verified in this release · ⏳ needs the production key, deployment or recordings.

## Product
- ✅ Home, worshipper and supervisor screens follow `docs/design/` (checked side by side in headless Edge at 390×844 and 1440×900)
- ✅ Portrait `bg-mobile.webp` / landscape `bg-desktop.webp`, `background-size: cover`
- ✅ Arabic RTL; Urdu RTL; English/Hindi LTR; no horizontal scroll at 390 px
- ✅ Live feed receives real backend segments; Quran cards show QuranEnc translator and version
- ✅ Ended → Replay; supervisor Result → Replay link

## Backend
- ✅ `/health`, `/ready`
- ✅ Broadcast code validated (constant-time), token required for audio/text/recorded/stop
- ✅ Listener counts per language, in memory only
- ✅ WebSocket reconnect without duplicates
- ✅ Temporary audio files deleted in `finally`
- ✅ Verified Quran translation used whenever a verse is detected; AI only for the khateeb's words
- ✅ Glossary hints + `glossary_warnings`

## Production
- ✅ Dockerfile (non-root, healthcheck), `render.yaml`, `.env.example`, `DEPLOY.md`
- ✅ No secrets / `.env` / recordings tracked by git
- ⏳ `OPENAI_API_KEY` and `MINBAR_BROADCAST_CODES` set on the host
- ⏳ HTTPS + `wss://` verified on the deployed URL from a second device/network

## Challenge evidence
- ⏳ Five real sermon recordings tested with `scripts/evaluate_sermons.py` (results into `docs/evaluation.md`)
- ✅ Test methodology documented (`docs/evaluation.md`)
- ✅ Source and verification documentation (`docs/sources.md`, README)
- ⏳ Live demo URL, two-minute video, presentation
