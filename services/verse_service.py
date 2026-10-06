"""Quran detection on top of verses.py, plus locating the quoted verse inside the
khateeb's sentence so his surrounding words are still translated."""

from __future__ import annotations

from rapidfuzz import fuzz

import verses
from verses import get_translation, match_verse, normalize

_BY_KEY = {(int(v["sura_no"]), int(v["aya_no"])): v for v in verses._CORPUS}

# Translator names as documented in docs/sources.md (QuranEnc packages).
TRANSLATORS = {
    "english_hilali_khan": {"ar": "تقي الدين الهلالي ومحمد محسن خان", "en": "Muhammad Taqi-ud-Din al-Hilali & Muhammad Muhsin Khan"},
    "urdu_junagarhi": {"ar": "محمد إبراهيم جوناكري", "en": "Muhammad Ibrahim Junagarhi"},
    "hindi_omari": {"ar": "عزيز الحق العمري", "en": "Azizul-Haq al-Omari"},
}

# Fewer remaining Arabic words than this around the verse means the sentence is
# essentially the verse itself (e.g. "قال تعالى ..."), so only the verified
# translation is shown.
_CONTEXT_MIN_WORDS = 3
_TRIM = " \t\n،,.:;؛«»\"'()﴿﴾-–—"


def _normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Same output as verses.normalize(), plus the original index of every kept char."""
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(text):
        if verses._DIACRITICS.match(ch) or verses._NON_ARABIC.match(ch):
            continue
        if ch.isspace():
            if not out or out[-1] == " ":
                continue
            ch = " "
        else:
            ch = ch.translate(verses._ALEF_MAP).replace("ى", "ي").replace("ة", "ه")
        out.append(ch)
        idx.append(i)
    if out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def _verse_span(text: str, verse_emlaey: str) -> tuple[int, int] | None:
    """(start, end) of the quoted verse in the original *text*, word-aligned."""
    sent_norm, idx = _normalize_with_map(text)
    verse_norm = normalize(verse_emlaey)
    if not sent_norm or len(verse_norm) >= len(sent_norm):
        return None  # the sentence is (part of) the verse
    al = fuzz.partial_ratio_alignment(verse_norm, sent_norm)
    if al is None or al.dest_end <= al.dest_start:
        return None
    start = idx[al.dest_start]
    end = idx[min(al.dest_end, len(idx)) - 1] + 1
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end].isspace():
        end += 1
    return start, end


# ── Embedded partial quotations ──────────────────────────────────────────────
# match_verse() compares the whole sentence with each verse, which misses a
# fragment of a long verse quoted inside the khateeb's commentary. A 3-word
# shingle index finds such fragments; strict length/coverage rules keep common
# Quranic phrases ("إن الله غفور رحيم") from being reported as a quotation.
_SHINGLE = 3
_EMBED_MIN_WORDS = 5
_EMBED_LONG_WORDS = 7
_EMBED_MIN_COVERAGE = 0.5
_EMBED_THRESHOLD = 90


def _build_index() -> tuple[list[tuple[dict, list[str]]], dict[str, list[int]]]:
    verses_words = [(v, n.split()) for v, n in verses._NORM_CORPUS]
    index: dict[str, list[int]] = {}
    for i, (_, words) in enumerate(verses_words):
        for j in range(len(words) - _SHINGLE + 1):
            index.setdefault(" ".join(words[j:j + _SHINGLE]), []).append(i)
    return verses_words, index


_VERSE_WORDS, _SHINGLE_INDEX = _build_index()


def _embedded_match(text: str) -> tuple[dict, int, int, float] | None:
    """(verse, first_word, end_word, score) of the best quoted fragment, using
    word positions in normalize(text)."""
    words = normalize(text).split()
    if len(words) < _EMBED_MIN_WORDS:
        return None
    positions: dict[int, list[int]] = {}
    for i in range(len(words) - _SHINGLE + 1):
        for v in set(_SHINGLE_INDEX.get(" ".join(words[i:i + _SHINGLE]), ())):
            positions.setdefault(v, []).append(i)

    best = None
    for v, pos in positions.items():
        # longest run of consecutive shingles = contiguous quoted words
        run_start, run_len, start, length = pos[0], 1, pos[0], 1
        for a, b in zip(pos, pos[1:]):
            if b == a + 1:
                length += 1
            else:
                start, length = b, 1
            if length > run_len:
                run_start, run_len = start, length
        covered = run_len + _SHINGLE - 1
        verse_len = len(_VERSE_WORDS[v][1])
        if covered < _EMBED_MIN_WORDS:
            continue
        window = " ".join(words[run_start:run_start + covered])
        if covered < _EMBED_LONG_WORDS and covered / verse_len < _EMBED_MIN_COVERAGE and not _unique(words[run_start:run_start + covered]):
            continue
        score = fuzz.partial_ratio(window, " ".join(_VERSE_WORDS[v][1]))
        if score < _EMBED_THRESHOLD:
            continue
        key = (covered, covered / verse_len, score)
        if best is None or key > best[0]:
            best = (key, v, run_start, run_start + covered, score)
    if best is None:
        return None
    _, v, first, end, score = best
    return _VERSE_WORDS[v][0], first, end, float(score)


def _unique(window: list[str]) -> bool:
    """A short fragment counts only if exactly one verse contains it, so stock
    phrases shared by many verses are not presented as a specific quotation."""
    shingles = [" ".join(window[i:i + _SHINGLE]) for i in range(len(window) - _SHINGLE + 1)]
    common = set(_SHINGLE_INDEX.get(shingles[0], ()))
    for sh in shingles[1:]:
        common &= set(_SHINGLE_INDEX.get(sh, ()))
    phrase = " ".join(window)
    return sum(phrase in " ".join(_VERSE_WORDS[v][1]) for v in common) == 1


def _word_span(text: str, first: int, end: int) -> tuple[int, int]:
    """Original-text (start, end) for normalized words [first, end)."""
    norm, idx = _normalize_with_map(text)
    starts = [0] + [i + 1 for i, ch in enumerate(norm) if ch == " "]
    ends = [i for i, ch in enumerate(norm) if ch == " "] + [len(norm)]
    start, stop = idx[starts[first]], idx[ends[end - 1] - 1] + 1
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while stop < len(text) and not text[stop].isspace():
        stop += 1
    return start, stop


def _source(lang: str, tr: dict) -> dict:
    data_meta = verses._load_translation(lang)["meta"]
    tid = data_meta.get("translation_id", "")
    names = TRANSLATORS.get(tid, {})
    return {
        "source": "QuranEnc",
        "translation_id": tid,
        "translator": names.get("en", tr.get("translator", "")),
        "translator_ar": names.get("ar", ""),
        "title": tr.get("translator", ""),
        "version": tr.get("version", ""),
        "url": data_meta.get("url", ""),
    }


def detect_verse(text: str, languages=("en", "ur", "hi")) -> dict | None:
    """Return verse info with verified translations, or None.

    Keys: sura, ayah, score, sura_name, arabic (Uthmani), translations, sources,
    verse_only, context {"before", "after"} (Arabic text around the quote).
    """
    text = text or ""
    span = None
    method = "sentence"
    match = match_verse(text)
    if match:
        verse = _BY_KEY.get((int(match["sura"]), int(match["ayah"])))
        if not verse:
            return None
        span = _verse_span(text, verse["aya_text_emlaey"])
    else:
        embedded = _embedded_match(text)
        if not embedded:
            return None
        verse, first, end, score = embedded
        method = "embedded"
        match = {"sura": verse["sura_no"], "ayah": verse["aya_no"], "score": score}
        span = _word_span(text, first, end)

    translations: dict[str, str] = {}
    sources: dict[str, dict] = {}
    for lang in languages:
        try:
            tr = get_translation(match["sura"], match["ayah"], lang)
        except (KeyError, FileNotFoundError):
            continue
        translations[lang] = tr["text"]
        sources[lang] = _source(lang, tr)

    before = after = ""
    if span:
        before = text[: span[0]].strip(_TRIM)
        after = text[span[1]:].strip(_TRIM)
    verse_only = len(normalize(f"{before} {after}").split()) < _CONTEXT_MIN_WORDS

    return {
        "sura": int(match["sura"]),
        "ayah": int(match["ayah"]),
        "score": round(float(match["score"]), 1),
        "method": method,
        "sura_name": verse.get("sura_name_ar", ""),
        "sura_name_en": verse.get("sura_name_en", ""),
        "arabic": verse.get("aya_text_unicode") or verse.get("aya_text_emlaey", ""),
        "translations": translations,
        "sources": sources,
        "verse_only": verse_only,
        "context": None if verse_only else {"before": before, "after": after},
    }
