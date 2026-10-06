# AI Methodology

This document explains where Minbar uses AI, where it deliberately does not, and what happens when AI fails.

> **AI is not used to freely generate Quran verse translations when a verified translation is available.** When a verse is detected, its translation is copied verbatim from the QuranEnc file for that language. AI only translates the khateeb's own words.

## 1. Summary

| Task | Method | AI? | Code |
|---|---|---|---|
| Arabic speech-to-text | OpenAI transcription, `language="ar"` | Yes | `services/speech_to_text.py` |
| Filtering silence artefacts and unusable output | Rule-based | No | `services/text_quality.py` |
| Sentence segmentation | Rule-based (punctuation, length, chunk count) | No | `services/segmenter.py` |
| Quran verse detection | Deterministic fuzzy matching against the Quran text | No | `verses.py`, `services/verse_service.py` |
| Quran verse translation | Verbatim lookup in QuranEnc files | No | `verses.get_translation` |
| Translation of the khateeb's speech | OpenAI Responses API | Yes | `services/translator.py` |
| Religious terminology | Glossary hint in the prompt + rule-based output check | Hint only | `validate.py` |
| Hadith label | Rule-based phrase markers; the hadith is **not** verified | No | `services/text_quality.py` |

## 2. Speech-to-text

- **Why AI:** live Arabic speech in a mosque (reverberation, varying microphones) needs a trained speech-recognition model.
- **Model:** `MINBAR_STT_MODEL`, default `whisper-1`, called through the official OpenAI Python SDK with `language="ar"`.
- **Input:** one complete audio file per chunk (6 s by default) or one recorded sermon file (up to 25 MB, the transcription endpoint's limit). Accepted formats: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC, MPEG/MPGA, OGA.
- **Handling of the audio:** written to a temporary file for the request and deleted afterwards in all cases. Nothing is kept.
- **Post-processing:** speech-to-text models sometimes emit subtitle-style phrases on silence (for example «اشتركوا في القناة»). These known artefacts are removed. Output that is not mostly Arabic is shown to worshippers as an "unclear segment" instead of being translated.

## 3. Translation of the khateeb's words

- **Why AI:** the khateeb's sermon is free speech; no fixed translation exists for it.
- **Model:** `MINBAR_TRANSLATION_MODEL`, default `gpt-5-mini`, via the Responses API. For `gpt-5*` and `o*` models, `reasoning.effort` is set from `MINBAR_TRANSLATION_REASONING_EFFORT` (default `minimal`); if the model rejects that parameter, the request is retried once without it.
- **Instructions** (`services/translator.py`): translate a live Friday sermon segment from Arabic into English, Urdu or Hindi; the input may be incomplete; preserve religious meaning, tone, names and honorifics; return only the translation, with no notes and no Arabic.
- **Parallelism:** the three languages are requested in parallel for each sentence. A failure in one language does not affect the others.
- **Commentary around a verse:** when a verse is quoted inside a longer sentence, only the khateeb's words before and after the quotation are sent to the model. The verse in the middle uses the verified translation, so the AI never sees or rewrites the verse text in that case.

## 4. Quran detection (no AI)

Detection is deterministic and runs locally on the Quran text of the King Fahd Complex (`data/kfgqpc_hafs_v30.json`, 6,236 verses).

1. **Normalisation** (`verses.normalize`): remove diacritics, tatweel and Quranic annotation marks; drop non-Arabic characters; unify alef forms (أ إ آ ٱ → ا), ى → ي and ة → ه.
2. **Whole-sentence match** (`verses.match_verse`): RapidFuzz `partial_ratio` between the normalised sentence and each normalised verse (`aya_text_emlaey`). A match needs at least 4 words and a score of at least 90. Verses shorter than 4 words (such as the disjoined letters «الم») are excluded as candidates so they cannot match any text trivially.
3. **Quotation inside commentary** (`services/verse_service._embedded_match`): a 3-word shingle index over the whole Quran finds the longest run of consecutive verse words inside the sentence. A run is accepted only if it covers at least 5 words and scores at least 90; a run shorter than 7 words must also cover at least half of the verse or be unique to a single verse. This stops common Quranic phrases (for example «إن الله على كل شيء قدير») from being presented as a citation of one specific verse.
4. **Context split:** the matched span is located in the original sentence. If fewer than 3 Arabic words remain around it, the sentence is treated as the verse alone (`verse_only`); otherwise the words before and after are kept for AI translation.

## 5. Verified Quran translations

When a verse is detected, the translation for each language is read from `data/translations/{en,ur,hi}.json` (QuranEnc, see [SOURCES.md](SOURCES.md)) and sent with its attribution: source, translator, title, version and URL. Worshippers see the Uthmani verse text (`aya_text_unicode`), the verified translation, and an attribution line under it. Arabic-mode readers see the Uthmani text only.

The verified translation is used even when AI is unavailable or failing.

## 6. Language adaptation

- Interface text (buttons, messages, errors) is a fixed, hand-written dictionary in four languages (`frontend/js/i18n.js`). It is not AI-generated at runtime.
- Arabic and Urdu are rendered right-to-left, English and Hindi left-to-right, per card, so sermon text keeps its own direction even when the interface language differs.
- Sermon language and interface language are independent choices.

## 7. Glossary and validation

`data/glossary.json` contains 10 core religious terms (Islam, tawhid, ibadah, nubuwwah, wahy, shariah, hadith, sunnah, fatwa, da'wah) with Arabic forms and approved English renderings.

- **Before translation:** terms whose Arabic forms appear in the sentence (whole word, or after a single attached clitic such as و ف ب ل ك) are listed in the prompt with their approved renderings.
- **After translation:** `validate.check_glossary` reports any such term whose approved rendering is missing from the output. These keys are returned as `glossary_warnings` in the segment (and by `/translate`). They are a quality signal; the translation is still delivered.
- **Coverage gap:** Urdu and Hindi renderings in the glossary are still empty, so hints and checks currently apply to English only.

## 8. When AI fails

| Situation | Behaviour |
|---|---|
| `OPENAI_API_KEY` missing | `/ready` reports `openai_configured: false` (and returns `503` in production). The supervisor page refuses to start an audio broadcast and explains that the key is missing. Audio endpoints return `503 ai_unavailable`. Text pipeline: verse detection and verified translations still work; AI translations are marked failed. |
| Key invalid or without permission | Speech-to-text returns `503 ai_key_invalid` with an actionable message. The supervisor page stops recording instead of retrying every chunk. Translations are marked failed. |
| Temporary OpenAI error or timeout | Speech-to-text returns `502 audio_processing_failed` for that chunk; the page retries it twice, then skips it and continues. The SDK itself retries twice with a 60 s timeout (`MINBAR_OPENAI_TIMEOUT_SECONDS`). |
| Translation fails for one language | That language is listed in `failed_languages`. The worshipper sees the Arabic text with a "translation unavailable" note; a detected verse still shows its verified translation. Other languages are unaffected. |
| Speech not recognised / not Arabic | The segment is shown as "unclear" rather than translated. |

## 9. Limitations

- **No accuracy guarantee.** Speech-to-text and AI translation can make mistakes. Every AI translation is labelled on screen as machine translation, with the khateeb's words as the reference.
- **Not yet measured on real sermon audio.** The automated tests do not call OpenAI. Speech-to-text accuracy, translation quality and end-to-end latency on real recordings have not been benchmarked yet; the method for doing so is in [TESTING.md](TESTING.md#5-evaluation-on-real-sermon-recordings).
- **AI output is not always complete.** In the replay screenshot ([`docs/screenshots/14-replay.png`](screenshots/14-replay.png)) the model left the opening formula «أما بعد» in Arabic. Output is not post-edited.
- **Verse detection depends on transcription quality.** A verse transcribed with many errors may not be detected and is then translated as ordinary speech. In testing, 1 of 150 embedded fragments matched a different verse.
- **Whole-verse translation for partial quotes.** When the khateeb quotes part of a long verse, the verified translation of the whole verse is shown, because verified translations are not split.
- **Glossary coverage** is small, English-only for now, and has not had a formal religious review.
- **Hadith are not verified.** The label only states that the khateeb cited a hadith.

## 10. Human review

Minbar is an accessibility aid, not a replacement for scholarly translation. Recommended practice:

- The mosque should treat the khateeb's Arabic as the authoritative text (the interface says so).
- Native speakers should review a sample of AI translations per language before relying on Minbar for regular use (see the review plan in [TESTING.md](TESTING.md#5-evaluation-on-real-sermon-recordings)).
- The glossary should be reviewed and extended by qualified reviewers; `data/glossary.json` has `reviewed_by` and `review_date` fields for this, currently empty.
