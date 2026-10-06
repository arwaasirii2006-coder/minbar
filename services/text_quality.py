"""Heuristics applied to raw speech-to-text output before it reaches worshippers."""

from __future__ import annotations

import re

from verses import normalize

_ARABIC_LETTER = re.compile(r"[ء-ي]")
_ANY_LETTER = re.compile(r"[^\W\d_]")

# Phrases speech-to-text models are known to emit on silence or background noise
# (video-subtitle artefacts). They never belong to a sermon, so they are removed.
_SILENCE_ARTEFACTS = [
    normalize(p)
    for p in (
        "ترجمة نانسي قنقر",
        "نانسي قنقر",
        "اشتركوا في القناة",
        "اشترك في القناة",
        "لا تنسوا الاشتراك في القناة",
        "لا تنسوا الاشتراك",
        "شكرا للمشاهدة",
        "شكرا على المشاهدة",
        "المترجم للقناة",
    )
]

_HADITH_MARKERS = [
    normalize(p)
    for p in (
        "قال رسول الله",
        "قال النبي",
        "عن النبي",
        "أن رسول الله",
        "سمعت رسول الله",
        "عن رسول الله",
        "قال صلى الله عليه وسلم",
    )
]


def arabic_word_count(text: str) -> int:
    return len(normalize(text or "").split())


def strip_silence_artefacts(text: str) -> str:
    """Remove known silence artefacts; returns '' when nothing else is left."""
    text = (text or "").strip()
    norm = normalize(text)
    found = False
    for phrase in _SILENCE_ARTEFACTS:
        if phrase in norm:
            norm = norm.replace(phrase, " ")
            found = True
    other_letters = len(_ANY_LETTER.findall(text)) - len(_ARABIC_LETTER.findall(text))
    if found and not norm.strip() and other_letters == 0:
        return ""
    return text


def classify(text: str) -> str:
    """'empty' (silence/nothing), 'unclear' (speech that is not usable Arabic) or 'ok'."""
    text = strip_silence_artefacts(text)
    letters = _ANY_LETTER.findall(text)
    if not letters:
        return "empty"
    arabic = _ARABIC_LETTER.findall(text)
    if len(arabic) < 4 or (letters and len(arabic) / len(letters) < 0.6):
        return "unclear"
    return "ok"


def looks_like_hadith(text: str) -> bool:
    norm = normalize(text or "")
    return any(marker in norm for marker in _HADITH_MARKERS)
