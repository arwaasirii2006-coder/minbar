# Demo Guide

A real end-to-end demo that takes **under two minutes**: supervisor → start broadcast → worshipper → choose language → live translation → end → replay.

## Using the live demo

The deployed instance is at **https://minbar-9kye.onrender.com** (worshipper: `/listen`, supervisor: `/broadcast`). Open it a minute before presenting: if it has been idle, the first load can take around half a minute while the instance starts. Broadcasting requires the mosque's broadcast code from the operator.

## Before the demo (5 minutes, once)

| Item | How |
|---|---|
| Server | Running locally ([QUICKSTART.md](QUICKSTART.md)) or the deployed HTTPS URL ([DEPLOYMENT.md](DEPLOYMENT.md)), with a valid `OPENAI_API_KEY`. `/ready` shows `"openai_configured": true`. |
| Broadcast code | The code you set for `KHATAM-2026` in `MINBAR_BROADCAST_CODES` |
| Supervisor device | A laptop with a microphone (`localhost` or HTTPS), or a phone on the HTTPS URL |
| Worshipper device | A second phone or browser window |
| Something to say | The script below, read aloud in Arabic, or a short recorded Arabic sermon file (≤ 25 MB) |
| Fresh room | If you already ran a broadcast in the last 2 hours, the worshipper page will open on "sermon ended". Restart the server (local) to reset the room. |

Suggested script (about 25 seconds). Sentence 2 is a hadith, sentence 3 a full verse (Āl-'Imrān 3:102), and sentence 4 quotes part of a verse (Fāṭir 35:28) inside the khateeb's commentary:

1. «أما بعد فيا عباد الله أوصيكم ونفسي بتقوى الله في السر والعلن.»
2. «قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات وإنما لكل امرئ ما نوى.»
3. «قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون.»
4. «أيها الإخوة الكرام تذكروا قول ربنا إنما يخشى الله من عباده العلماء فالعلم طريق الخشية والتقوى.»

Speak at a normal pace and pause briefly at the end of each sentence.

## The demo, step by step

| Time | Who | Action | What the audience sees |
|---|---|---|---|
| 0:00 | Supervisor | Open `/broadcast`, select **جامع الخطام**, enter the code, **Sign in** | Ready screen ([screenshot](screenshots/06-broadcast-ready.png)): microphone level bars, waiting worshippers per language |
| 0:15 | Worshipper | Open `/listen` (or `/listen?room=KHATAM-2026`), **Start** | Welcome screen with a greeting rotating through four languages |
| 0:20 | Worshipper | Choose **English** (or Urdu/Hindi/Arabic), **Continue** | Waiting screen with "Connected" ([screenshot](screenshots/04-waiting.png)). The supervisor's count shows 1 in that language |
| 0:30 | Supervisor | **Start broadcast** | Timer starts; the worshipper's screen switches to live |
| 0:35 | Speaker | Read the four sentences | Every ~6 s the supervisor sees the detected Arabic text ([screenshot](screenshots/11-broadcasting.png)). The worshipper sees sentences appear in order: a plain card, a card labelled "Hadith as cited by the khateeb", and **gold Quran cards** with the Uthmani verse, the verified QuranEnc translation and the translator's name. The last card shows the khateeb's commentary translated around the quoted verse ([screenshot](screenshots/07-live-english.png)) |
| 1:15 | Worshipper | Tap the language pill at the top and switch to **Urdu** | The whole log re-renders in Urdu, right-to-left, without reconnecting ([screenshot](screenshots/08-live-urdu.png)); the supervisor's per-language count moves |
| 1:30 | Supervisor | **Stop broadcast** | Supervisor: duration, peak listeners, verified verses, unclear segments ([screenshot](screenshots/12-broadcast-ended.png)). Worshipper: "The sermon has ended." with a closing supplication ([screenshot](screenshots/13-sermon-ended.png)) |
| 1:40 | Worshipper | **Read the sermon again** | The full sermon in the selected language ([screenshot](screenshots/14-replay.png)) |

Total: about 1 minute 45 seconds.

Points worth saying out loud:

- The worshipper created no account and typed nothing.
- The verse translation is not AI output: it is the verified QuranEnc translation, attributed on the card.
- Only the khateeb's own words are machine-translated, and the page says so at the bottom.

## Testing the four languages

To show all four at once, open four worshipper tabs or windows before starting (the sermon language is stored per tab, in `sessionStorage`) and pick one language in each:

| Window | Choose | Expected for the verse sentence |
|---|---|---|
| 1 | **العربية** (sermon text, for hearing-impaired worshippers) | Uthmani verse text, no translation box ([screenshot](screenshots/10-live-arabic-text.png)) |
| 2 | **English** | Translation by al-Hilali & Khan, left-to-right |
| 3 | **اردو** | Translation by Junagarhi, right-to-left |
| 4 | **हिन्दी** | Translation by al-Omari, left-to-right ([screenshot](screenshots/09-live-hindi.png)) |

The supervisor's card shows `1` under each language. The interface language (menus, buttons) is a separate choice from the globe menu at the top of every page, so an Urdu speaker can, for example, use an English interface and read the sermon in Urdu.

## If something goes wrong during the demo

| Problem | Quick recovery |
|---|---|
| Microphone permission prompt was dismissed | Use **Try again**, or switch to **Audio file** and upload a recording |
| Red status "The OpenAI key on the server is invalid…" | The key is wrong: fix it and restart. For a demo without speech, see the text option below |
| Worshipper page opens on "sermon ended" | A previous demo ended less than 2 hours ago: restart the local server |
| Nothing appears for a long pause | Sentences are published at punctuation or after two chunks (~12 s) of speech; keep talking |

**Demo without a microphone.** Start the broadcast through the API instead of the supervisor page, then send Arabic sentences; they go through the same pipeline used after speech-to-text (verse detection, verified translations, AI translation, ordered delivery):

```bash
# 1. Start (the response contains "broadcaster_token")
curl -X POST http://127.0.0.1:8000/broadcast/start   -H "Content-Type: application/json"   -d '{"room_id": "KHATAM-2026", "code": "YOUR_CODE"}'

# 2. Send a sentence
curl -X POST http://127.0.0.1:8000/live/KHATAM-2026/text   -H "X-Broadcaster-Token: TOKEN_FROM_STEP_1"   --data-urlencode "arabic=قال تعالى يا أيها الذين آمنوا اتقوا الله حق تقاته ولا تموتن إلا وأنتم مسلمون."

# 3. Stop
curl -X POST http://127.0.0.1:8000/broadcast/KHATAM-2026/stop -H "X-Broadcaster-Token: TOKEN_FROM_STEP_1"
```

If your terminal cannot send Arabic reliably (some Windows shells), use the interactive API docs at `http://127.0.0.1:8000/docs` (development mode) instead. The screenshots in `docs/screenshots/` were produced with step 2, while the broadcast was started from the supervisor page.
