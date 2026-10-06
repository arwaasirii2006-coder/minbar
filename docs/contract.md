# عقد بيانات منبر

يصف هذا الملف الشكل المتعاقد عليه للبيانات التي يستخدمها الخادم.

---

## اللغات المدعومة

| الرمز | اللغة | الملف |
|---|---|---|
| `en` | إنجليزية | `data/translations/en.json` |
| `ur` | أردية | `data/translations/ur.json` |
| `hi` | هندية | `data/translations/hi.json` |

---

## بيانات القرآن — `data/kfgqpc_hafs_v30.json`

قائمة JSON من 6236 عنصراً، كل عنصر يمثل آية. الحقول المستخدمة:

| الحقل | النوع | الوصف |
|---|---|---|
| `sura_no` | integer | رقم السورة (1–114) |
| `aya_no` | integer | رقم الآية داخل السورة |
| `sura_name_ar` | string | اسم السورة بالعربية |
| `aya_text_emlaey` | string | نص الآية بالرسم الإملائي (للبحث والمعالجة) |
| `aya_text_unicode` | string | نص الآية بالرسم العثماني المُشكَّل (للعرض) |

---

## بيانات الترجمات — `data/translations/{lang}.json`

كائن JSON بالشكل:

```json
{
  "meta": {
    "header": "...",
    "language": "...",
    "translation_id": "...",
    "source": "...",
    "url": "...",
    "last_update": "...",
    "source_file": "..."
  },
  "1:1": "...",
  "1:2": "...",
  "2:255": "...",
  ...
}
```

### مفتاح الآية

المفتاح هو `"سورة:آية"` بالأرقام العربية المعيارية، مثال: `"2:255"` للآية 255 من سورة البقرة.

يطابق المفتاح دائماً `sura_no:aya_no` في ملف القرآن، ويغطي جميع الآيات الـ 6236.

### ضمانات التحويل

- الترويسة الأصلية محفوظة حرفاً بحرف في `meta.header`.
- أرقام الحواشي مثل `[1]` محذوفة؛ عمود `footnotes` غير منقول.
- الرقم في بداية الآية الإنجليزية (مثل `"1. "`) محذوف.
- لا يوجد نص فارغ ولا مسافات مزدوجة.

---

## مسرد المصطلحات — `data/glossary.json`

```json
{
  "meta": { ... },
  "terms": {
    "<term_key>": {
      "ar": ["..."],
      "en": ["..."],
      "ur": [],
      "hi": [],
      "rule": "..."
    }
  }
}
```

حقل `hi` يقابل اللغة الهندية (رمز `hi` في الترجمات).

---

## واجهة HTTP

كل خطأ بالشكل: `{"detail": {"code": "...", "message": "..."}}`.

| الطريقة | المسار | الوصف | أخطاء |
|---|---|---|---|
| GET | `/` `/listen` `/broadcast` `/privacy` | الصفحات | |
| GET | `/health` | `{status, version, live_rooms}` | |
| GET | `/ready` | فحص البيانات والأسرار | 503 `not_ready` |
| GET | `/broadcast/mosques` | `{mosques:[{id,name,location}]}` | |
| POST | `/broadcast/verify` | `{room_id, code}` ← `{valid, room, config}` | 400 `missing_code` · 403 `invalid_code` · 404 `unknown_mosque` · 503 `codes_not_configured` |
| POST | `/broadcast/start` | `{room_id, code, khateeb?, resume?}` ← الحالة + `broadcaster_token` + `config` | 409 `already_live` |
| GET | `/broadcast/{room_id}` | الحالة العامة: `status, session, listeners, language_counts, segments, processing` | 404 `unknown_room` |
| POST | `/broadcast/{room_id}/stop` | يتطلب `X-Broadcaster-Token` ← الإحصاءات | 401 · 409 `already_ended` / `not_live` |
| GET | `/broadcast/{room_id}/replay` | مقاطع الجلسة الحالية أو المنتهية | |
| POST | `/live/{room_id}/audio` | مقطع صوتي (multipart `file`) ← `{type: chunk/empty/unclear/discarded}` | 400 `empty_audio` · 413 `file_too_large` · 415 `unsupported_audio` · 502/503 |
| POST | `/live/{room_id}/text` | `arabic` (form) لنص عربي جاهز | |
| POST | `/live/{room_id}/recorded` | خطبة مسجلة ← 202 `{type: processing}`، والتقدّم عبر WebSocket و `GET /broadcast/{id}` | 409 `processing` |
| POST | `/transcribe` | `file`, `target_language` ← `{original_text, translation, verse, ...}` | 400 `unsupported_language` |
| POST | `/transcribe_all` | `file` ← `{original_text, en, ur, hi, verse, ...}` | |
| POST | `/translate` | `{text, target_language}` ← `{translation, verse, glossary_warnings}` | 400 · 502 `translation_failed` |
| POST | `/detect_verse` | `{text}` ← `{verse}` بلا ذكاء اصطناعي | |

في الإنتاج تتطلب `/transcribe` و `/transcribe_all` و `/translate` رمز مذيع نشط.

## WebSocket `/ws/{room_id}`

معاملات: `role=listener|broadcaster`، `language=ar|en|ur|hi`، `token` (للمذيع)، `since` و `session` (لإعادة الاتصال).

رموز الإغلاق: `4404` جامع غير موجود، `4401` مذيع بلا صلاحية.

| من الخادم | المحتوى |
|---|---|
| `state` | الحالة العامة + `language` |
| `history` | `{session, segments}` ما فات المستمع في الجلسة نفسها، أو الجلسة كاملة |
| `started` | `{session, khateeb, started_at}` |
| `segment` | انظر أدناه |
| `ended` | `{stats}` |
| `listeners` | (للمذيع) `{count, language_counts, peak}` |
| `processing` | (للمذيع) تقدّم الخطبة المسجلة |
| `error` | `{code, message}`: `unknown_room` · `unauthorized` · `unsupported_language` |
| `pong` | رد على `ping` |

| من العميل | المحتوى |
|---|---|
| `{"type":"ping"}` | إبقاء الاتصال (كل 25 ثانية) |
| `{"type":"language","language":"ur"}` | تغيير لغة المستمع دون إعادة اتصال |

### رسالة `segment`

```json
{
  "type": "segment", "seq": 3, "id": "KHATAM-2026-1-3", "ts": 1791234567890,
  "arabic": "النص العربي كما نُطق",
  "is_unclear": false,
  "is_hadith": false,
  "translations": {"en": "...", "ur": "...", "hi": "..."},
  "failed_languages": [],
  "glossary_warnings": {"en": ["tawhid"]},
  "parts": {"en": {"before": "...", "after": "..."}},
  "verse": {
    "sura": 3, "ayah": 102, "score": 98.5, "method": "sentence",
    "sura_name": "آلِ عِمۡرَانَ", "sura_name_en": "Āl-‘Imrān",
    "arabic": "النص العثماني",
    "translations": {"en": "...", "ur": "...", "hi": "..."},
    "sources": {"en": {"source": "QuranEnc", "translation_id": "english_hilali_khan", "translator": "...", "translator_ar": "...", "version": "...", "url": "..."}},
    "verse_only": true,
    "context": null
  }
}
```

- `verse_only=false`: الجملة فيها كلام للخطيب حول الآية. `verse.context` يحمل النص العربي قبلها وبعدها، و `parts` ترجمته بالذكاء الاصطناعي.
- `translations[lang]` نص كامل جاهز للعرض البسيط، وترجمة الآية فيه بين علامتي تنصيص.
