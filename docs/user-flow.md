# Minbar — User Flow

## Worshipper (`/listen`)

```text
Home (/) → Welcome → Language → Waiting → Live Translation → Sermon Ended → Replay
                                   ↑            │
                                   └── language can be changed at any time (no reconnect)
```

- A language chosen earlier in the same browser session skips Welcome and Language.
- `READY` → Waiting; `LIVE` → Live (history of the session is loaded); `ENDED` → Ended.
- Disconnect → orange banner «انقطع الاتصال، جارٍ إعادة الاتصال. لن يفوتك شيء.», faded cards, automatic reconnect with backoff; missed segments are delivered once.
- Unknown mosque link → clear message, no retry loop.
- Replay reads the temporary in-memory transcript while it is retained.

## Mosque supervisor (`/broadcast`)

```text
Login (mosque + broadcast code) → Ready → Microphone permission → Broadcasting → Broadcast Ended
                                    │
                                    └─ Recorded file → Processing → Result → Replay link
```

Error branches handled in the UI and API:

| Case | Behaviour |
|---|---|
| Invalid broadcast code | red field + «الرمز غير صحيح.» (403) |
| Microphone permission denied | 3-step iPhone/iPad guide, retry, or upload a recording |
| Insecure page (no HTTPS) | explains that the microphone needs https |
| Network disconnect | chunks queue and resend; status line explains |
| Audio processing / translation failure | chunk skipped after retries, broadcast continues |
| Empty / unsupported / too large audio | 400 / 415 / 413 with message |
| Broadcast already live | 409 → offer to continue on this device (token rotated) |
| Broadcast already ended | 409 `already_ended` |
| Session moved to another device | supervisor sees the reason and returns to Ready |

## Session states

```text
READY ──start──▶ LIVE ──stop──▶ ENDED ──TTL──▶ READY
                  ▲                │
                  └────start───────┘   (new session, previous transcript cleared)
```
