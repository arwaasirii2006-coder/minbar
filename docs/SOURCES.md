# Content Sources and Verification

Every content file Minbar uses is listed here with its origin, purpose, how the code uses it and how it was verified. No other content sources are used.

## 1. Quran text

| Field | Value |
|---|---|
| File | `data/kfgqpc_hafs_v30.json` (6,236 entries, one per verse) |
| Source | King Fahd Glorious Qur'an Printing Complex — [Developers portal](https://qurancomplex.gov.sa/quran-dev/) |
| Package | Unicode computer script, Hafs narration, version 30 (`kfgqpc_hafs_v30.zip`) |
| Published SHA-256 of the zip | `227E6B1564D980F2BD09C2C35EBFB0330AC268C79A7C247CD1AB665BC635F245` |
| Purpose | Reference text for verse detection and the Uthmani verse shown to worshippers |
| How used | `aya_text_emlaey` (simplified spelling) is normalised and matched against the transcript (`verses.py`, `services/verse_service.py`). `aya_text_unicode` (Uthmani, with diacritics) is displayed. `sura_name_ar` / `sura_name_en` label the verse card. |

**Verification (4 October 2026):**

| Check | Result |
|---|---|
| SHA-256 of `kfgqpc_hafs_v30.zip` matches the published value | ✅ |
| Number of entries | ✅ 6,236 |
| Surahs (`sura_no`) | ✅ 114 (1 to 114) |
| Empty or missing `aya_text_emlaey` | ✅ none |
| Duplicate `id` | ✅ none |
| Zip integrity | ✅ no corrupt members |
| JSON inside the zip identical to the copy in `data/` | ✅ same SHA-256 (`d7adf8ae…f4d3`) |

Runtime check: `GET /ready` reports `quran_corpus: true` only when exactly 6,236 verses are loaded.

## 2. Verified translations of the meanings of the Quran

| Language | File | Translator | Version | Source |
|---|---|---|---|---|
| English | `data/translations/en.json` | Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan (`english_hilali_khan`) | v1.1.2 (2025-09-04) | [quranenc.com/en/browse/english_hilali_khan](https://quranenc.com/en/browse/english_hilali_khan) |
| Urdu | `data/translations/ur.json` | Muhammad Ibrahim Junagarhi (`urdu_junagarhi`) | v1.1.3 (2025-08-13) | [quranenc.com/en/browse/urdu_junagarhi](https://quranenc.com/en/browse/urdu_junagarhi) |
| Hindi | `data/translations/hi.json` | Azizul-Haq al-Omari (`hindi_omari`) | v1.1.5 (2025-08-05) | [quranenc.com/en/browse/hindi_omari](https://quranenc.com/en/browse/hindi_omari) |

| Field | Value |
|---|---|
| Purpose | The only translation shown for a detected verse |
| How used | `verses.get_translation(sura, ayah, lang)` returns the text verbatim; `services/verse_service.py` attaches source, translator, title, version and URL, which the worshipper sees under the verse |
| Conversion | `data/convert_translations.py` converts the QuranEnc CSV downloads (kept out of git in `data/raw/`) into JSON: the `Translation Info` header is kept verbatim in `meta.header`; the leading verse number and footnote markers such as `[1]` are removed; footnotes are not carried over; no other text is changed. The script asserts 6,236 verses, no duplicates and no leftover markers. |

**Verification (4 October 2026):**

| Check | en | ur | hi |
|---|---|---|---|
| Number of verses | ✅ 6,236 | ✅ 6,236 | ✅ 6,236 |
| Verse keys match `kfgqpc_hafs_v30.json` | ✅ | ✅ | ✅ |
| `Translation Info` header copied verbatim | ✅ | ✅ | ✅ |
| Remaining footnote markers | ✅ 0 | ✅ 0 | ✅ 0 |
| Double spaces | ✅ 0 | ✅ 0 | ✅ 0 |
| All other characters of the source preserved | ✅ | ✅ | ✅ |
| Translation also listed on quranpedia.net | ✅ | ✅ | ✅ |
| Verse 1:2 matches quranpedia.net | ✅ | ✅ | ✅ |

Runtime check: `GET /ready` reports `translations: true` only when all three files load with every verse. `tests/test_verses.py` checks lookups and attribution.

## 3. Terminology glossary

| Field | Value |
|---|---|
| File | `data/glossary.json` |
| Source | Core terminology dictionary templates in the scientific reference pack of the challenge ("نماذج قاموس المصطلحات الأساسية — المرجعية والحزمة العلمية والبيانات، تحدي الذكاء الاصطناعي في خدمة المحتوى الإسلامي", version 20/3/1448) |
| To be completed from | [Al-Jamhara dictionary — islamic-content.com/dictionary](https://islamic-content.com/dictionary) |
| Content | 10 terms: `islam`, `tawhid`, `ibadah`, `nubuwwah`, `wahy`, `shariah`, `hadith`, `sunnah`, `fatwa`, `dawah`. Each has Arabic forms, approved English renderings, a usage rule, and Urdu/Hindi lists |
| Purpose | Guide and check the AI translation of religious terms |
| How used | `validate.py` finds terms in the Arabic text; `services/translator.py` adds their approved renderings to the prompt; the output is checked and missing terms are returned as `glossary_warnings` (see [AI.md](AI.md#7-glossary-and-validation)) |
| Status | Preliminary. Urdu and Hindi renderings are empty until taken from an approved source. `reviewed_by` and `review_date` are empty: **no formal religious review yet** |
| Note | The template's Bengali (`bn`) column was mapped to Hindi (`hi`) to match the project's languages |
| Verification | `tests/test_validate.py` (41 tests) covers matching with clitics, false-positive avoidance and missing-term detection |

## 4. Scientific reference

| Field | Value |
|---|---|
| File | `docs/scientific-reference-pack.pdf` |
| Description | The challenge's scientific reference and data pack. The sources above were chosen according to it. |

## 5. Sermon content

The repository contains **no sermon recordings and no sermon transcripts**. Live sermon audio exists only for the duration of one transcription request (see [PRIVACY.md](PRIVACY.md)). `.gitignore` excludes audio formats and the `demo-recordings/` and `recordings/` folders. Recordings used for evaluation must stay outside the repository ([`scripts/evaluate_sermons.py`](../scripts/evaluate_sermons.py) reads them from any local path).

## 6. Mosque directory

| Field | Value |
|---|---|
| File | `data/mosques.json` |
| Content | One demo mosque: `KHATAM-2026`, جامع الخطام, Asir, Saudi Arabia |
| Purpose | Defines which broadcast rooms exist and the name/location shown to worshippers |
| Note | Public data only. The secret broadcast codes are not in this file; they come from the `MINBAR_BROADCAST_CODES` environment variable |

## 7. Test data

| Data | Where | Origin |
|---|---|---|
| Arabic sermon-style sentences, verse quotations (e.g. Āl-'Imrān 3:102, Fāṭir 35:28), common non-verse phrases | Inline in `tests/*.py` and `tests/browser/*.py` | Written for the tests; verse text taken from the Quran file above |
| Audio test data | pytest generates silent WAV bytes in memory (`wav_bytes()` in `tests/test_final_api.py`) and, where speech-to-text must succeed, replaces the OpenAI client with a fake; the browser suites record a test tone from Chromium's simulated microphone | No real voice recordings |
| Broadcast code | `test-code-123` (pytest), `demo-4821` (browser suites, configurable) | Test values only, not used by any deployment |

---

Data verification: 4 October 2026, by Arwa Asiri.
