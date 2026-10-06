"""verses.py – Quran verse detection and translation lookup.

Public API
----------
normalize(text)                       -> str
match_verse(text, threshold, min_words) -> {"sura", "ayah", "score"} | None
get_translation(sura, ayah, lang)     -> {"text", "translator", "version", "lang"}
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from rapidfuzz import fuzz, process

_DATA = Path(__file__).resolve().parent / "data"

# ── Normalisation ─────────────────────────────────────────────────────────────

# Tashkeel, tatweel (kashida), and other Arabic combining marks
_DIACRITICS = re.compile(
    r"[ؐ-ؚ"   # Arabic extended letters used as marks
    r"ً-ٟ"   # harakat, shadda, sukun …
    r"ٰ"           # superscript alef
    r"ـ"           # tatweel  ـ
    r"ۖ-ۭ]"  # Quranic annotation signs
)

# Alef forms → plain alef (U+0627)
_ALEF_MAP = str.maketrans("أإآٱ", "اااا")

# Keep Arabic base letters (U+0621–U+063A, U+0641–U+0671) and whitespace
_NON_ARABIC = re.compile(r"[^ء-غف-ٱ\s]")


def normalize(text: str) -> str:
    """Remove diacritics, tatweel, and punctuation; unify letter variants.

    Transformations applied (in order):
    1. Strip tashkeel, tatweel, Quranic marks.
    2. Drop non-Arabic, non-space characters (digits, Latin, punctuation …).
    3. Unify alef forms (أ إ آ ٱ) → ا.
    4. Unify ى → ي.
    5. Unify ة → ه.
    6. Collapse whitespace.
    """
    text = _DIACRITICS.sub("", text)
    text = _NON_ARABIC.sub("", text)
    text = text.translate(_ALEF_MAP)
    text = text.replace("ى", "ي")
    text = text.replace("ة", "ه")
    return re.sub(r"\s+", " ", text).strip()


# ── Corpus (loaded once at import time) ───────────────────────────────────────

def _load_corpus() -> list[dict]:
    with open(_DATA / "kfgqpc_hafs_v30.json", encoding="utf-8") as f:
        return json.load(f)


_CORPUS: list[dict] = _load_corpus()

# Pre-normalise every emlaey text to avoid repeating work per query
_NORM_CORPUS: list[tuple[dict, str]] = [
    (v, normalize(v["aya_text_emlaey"])) for v in _CORPUS
]


# ── Verse matching ─────────────────────────────────────────────────────────────

def match_verse(
    text: str,
    threshold: int = 90,
    min_words: int = 4,
) -> Optional[dict]:
    """Return the best-matching Quranic verse or None.

    Matching is done via rapidfuzz.fuzz.partial_ratio on normalised text.
    partial_ratio handles partial quotations: it slides the shorter string
    over the longer one and returns the best window score.

    Acceptance conditions:
      - The normalised input contains at least *min_words* whitespace-delimited
        tokens (filters out isolated words or very short fragments).
      - The best partial_ratio score is >= *threshold*.

    Returns
    -------
    dict with keys ``sura`` (int), ``ayah`` (int), ``score`` (float), or None.
    """
    norm = normalize(text)
    if len(norm.split()) < min_words:
        return None

    # Skip candidate verses whose normalised text is shorter than the
    # minimum-word threshold: single-letter muqatta'at (e.g. "الم") would
    # otherwise score 100 on any Arabic text as a trivial substring.
    verses_, choices = _candidates(min_words)
    # extractOne runs the same partial_ratio scan in C and keeps the first best
    # match, exactly like the original Python loop.
    best = process.extractOne(norm, choices, scorer=fuzz.partial_ratio, processor=None, score_cutoff=threshold)
    if best is None:
        return None
    _, best_score, index = best

    if best_score >= threshold:
        best_verse = verses_[index]
        return {
            "sura": best_verse["sura_no"],
            "ayah": best_verse["aya_no"],
            "score": best_score,
        }
    return None


@lru_cache(maxsize=4)
def _candidates(min_words: int) -> tuple[list[dict], list[str]]:
    kept = [(v, n) for v, n in _NORM_CORPUS if len(n.split()) >= min_words]
    return [v for v, _ in kept], [n for _, n in kept]


# ── Translation lookup ────────────────────────────────────────────────────────

@lru_cache(maxsize=8)
def _load_translation(lang: str) -> dict:
    if lang not in {"en", "ur", "hi"}:
        raise KeyError(lang)
    path = _DATA / "translations" / f"{lang}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_translation(sura: int, ayah: int, lang: str) -> dict:
    """Return the translation of a verse with attribution metadata.

    Parameters
    ----------
    sura  : Sura number (1–114).
    ayah  : Verse number within the sura.
    lang  : Language code – one of ``"en"``, ``"ur"``, ``"hi"``.

    Returns
    -------
    dict with keys:
      ``text``       – translation string,
      ``translator`` – translator name(s) from meta.title,
      ``version``    – last_update string from meta,
      ``lang``       – the requested language code.

    Raises
    ------
    KeyError  if *lang* is unsupported or the verse key is absent.
    FileNotFoundError  if the translation file does not exist.
    """
    data = _load_translation(lang)
    key = f"{sura}:{ayah}"
    return {
        "text": data[key],
        "translator": data["meta"].get("title", ""),
        "version": data["meta"].get("last_update", ""),
        "lang": lang,
    }
