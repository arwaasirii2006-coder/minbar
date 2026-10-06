"""Arabic sentence → listener segment.

    classify → Quran detection → verified Quran translation (verse) +
    AI translation (the khateeb's own words) → segment payload

A failure in one language never blocks the others or the Arabic text.
"""

from __future__ import annotations

import asyncio

from services.config import TRANSLATION_LANGUAGES
from services.text_quality import classify, looks_like_hadith
from services.translator import TranslationError, translate_text
from services.verse_service import detect_verse


async def _ai(text: str, lang: str) -> tuple[str, list[str]]:
    if not text.strip():
        return "", []
    return await asyncio.to_thread(translate_text, text, lang)


async def _translate_one(arabic: str, lang: str, verse: dict | None) -> dict:
    verified = (verse or {}).get("translations", {}).get(lang, "")
    try:
        if verse and verified and verse["verse_only"]:
            return {"text": verified, "warnings": [], "parts": None, "failed": False}
        if verse and verified and verse.get("context"):
            ctx = verse["context"]
            (before, w1), (after, w2) = await asyncio.gather(_ai(ctx["before"], lang), _ai(ctx["after"], lang))
            text = " ".join(x for x in (before, f"“{verified}”", after) if x)
            return {"text": text, "warnings": w1 + w2, "parts": {"before": before, "after": after}, "failed": False}
        text, warnings = await _ai(arabic, lang)
        return {"text": text, "warnings": warnings, "parts": None, "failed": False}
    except TranslationError:
        # The verified verse translation (if any) is still delivered.
        return {"text": f"“{verified}”" if verified else "", "warnings": [], "parts": None, "failed": True}


def unclear_segment() -> dict:
    return {
        "type": "segment", "arabic": "", "is_unclear": True, "is_hadith": False, "verse": None,
        "translations": {}, "parts": {}, "failed_languages": [], "glossary_warnings": {},
    }


async def build_segment(arabic: str, languages=TRANSLATION_LANGUAGES) -> dict | None:
    """Return the segment payload (without seq/id/ts), or None for silence."""
    arabic = (arabic or "").strip()
    kind = classify(arabic)
    if kind == "empty":
        return None
    if kind == "unclear":
        return unclear_segment()

    verse = await asyncio.to_thread(detect_verse, arabic, tuple(languages))
    results = await asyncio.gather(*(_translate_one(arabic, lang, verse) for lang in languages))
    by_lang = dict(zip(languages, results))

    return {
        "type": "segment",
        "arabic": arabic,
        "is_unclear": False,
        "is_hadith": verse is None and looks_like_hadith(arabic),
        "verse": verse,
        "translations": {lang: r["text"] for lang, r in by_lang.items()},
        "parts": {lang: r["parts"] for lang, r in by_lang.items() if r["parts"]},
        "failed_languages": [lang for lang, r in by_lang.items() if r["failed"]],
        "glossary_warnings": {lang: r["warnings"] for lang, r in by_lang.items() if r["warnings"]},
    }
