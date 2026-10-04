"""validate.py – Glossary compliance checker for translated segments.

Public API
----------
check_glossary(arabic, translated, lang) -> list[str]
    Returns a list of glossary term keys whose Arabic forms appear in *arabic*
    but whose accepted translations are absent from *translated*.
    An empty list means the translation is compliant.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from verses import normalize

_DATA = Path(__file__).resolve().parent / "data"


# ── Glossary (loaded once) ────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _load_glossary() -> dict:
    with open(_DATA / "glossary.json", encoding="utf-8") as f:
        return json.load(f)


def _glossary_terms() -> dict:
    return _load_glossary()["terms"]


# ── Helpers ───────────────────────────────────────────────────────────────────

# Single-character Arabic clitics that attach directly to the following word
# (conjunctions و ف, prepositions ب ل ك).  A glossary form preceded by one of
# these in the text still counts as a match.
_CLITIC = r"[وفبلك]"
# A form is present when preceded by start-of-string, whitespace, or a clitic,
# AND followed by end-of-string or whitespace (never mid-word).
_FORM_RE_TPL = r"(?:(?:^|(?<=\s))|(?<={clitic})){form}(?=\s|$)"


def _arabic_present(ar_forms: list[str], norm_arabic: str) -> bool:
    """True if any normalised Arabic form appears as a whole word (or after a
    single clitic) in *norm_arabic*.

    Handles attached clitics (و ف ب ل ك) so 'التوحيد' matches 'والتوحيد',
    while avoiding spurious matches such as 'وحي' inside 'والتوحيد'.
    """
    for form in ar_forms:
        nf = normalize(form)
        if not nf:
            continue
        # Build a pattern that requires the form to start after a word boundary
        # (space / start-of-string) or after a single clitic character, and to
        # end before a word boundary (space / end-of-string).
        pattern = (
            r"(?:(?:^|\s)"        # preceded by start or space …
            + re.escape(nf)
            + r"(?:\s|$)"         # … followed by space or end
            + r"|"
            + r"(?<=" + _CLITIC + r")"  # OR preceded by a clitic
            + re.escape(nf)
            + r"(?:\s|$))"
        )
        if re.search(pattern, norm_arabic):
            return True
    return False


def _translation_present(accepted: list[str], translated: str, lang: str) -> bool:
    """True if any accepted translation appears in the translated text.

    For English (``lang == "en"``) the comparison is case-insensitive.
    For all other languages it is an exact substring match.
    """
    if lang == "en":
        translated_cmp = translated.lower()
        return any(t.lower() in translated_cmp for t in accepted)
    return any(t in translated for t in accepted)


# ── Public function ───────────────────────────────────────────────────────────

def check_glossary(arabic: str, translated: str, lang: str) -> list[str]:
    """Return keys of glossary terms that are missing in *translated*.

    Parameters
    ----------
    arabic     : Source Arabic text (un-normalised is fine).
    translated : Translation of *arabic* in the target language.
    lang       : Language code – ``"en"``, ``"ur"`` or ``"hi"``.

    Algorithm
    ---------
    For every term in data/glossary.json:
    1. Skip the term if its translation list for *lang* is empty.
    2. Normalise the Arabic text and check whether any of the term's Arabic
       forms appears as a whole word.
    3. If the Arabic form is present but none of the accepted translations
       appears in *translated*, add the term's key to the missing list.

    Returns
    -------
    List of term keys (strings) that are unaccounted for, in glossary order.
    Empty list → translation is compliant.
    """
    norm_arabic = normalize(arabic)
    missing: list[str] = []

    for key, term in _glossary_terms().items():
        accepted = term.get(lang, [])
        if not accepted:
            # No authorised translations for this lang yet – skip
            continue
        if _arabic_present(term["ar"], norm_arabic):
            if not _translation_present(accepted, translated, lang):
                missing.append(key)

    return missing
