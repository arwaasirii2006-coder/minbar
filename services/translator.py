"""AI translation of the khateeb's non-Quranic speech, guided and checked by the
project glossary (data/glossary.json via validate.py)."""

from __future__ import annotations

import logging

from services.config import LANGUAGE_NAMES, TRANSLATION_LANGUAGES, translation_model, translation_reasoning_effort
from services.openai_client import AIUnavailable, get_client
from validate import _glossary_terms, check_glossary

log = logging.getLogger("minbar")


class TranslationError(RuntimeError):
    pass


def _glossary_hint(arabic: str, lang: str) -> str:
    # With an empty translation, check_glossary returns exactly the terms present
    # in the Arabic text that have approved renderings for this language.
    present = check_glossary(arabic, "", lang)
    if not present:
        return ""
    terms = _glossary_terms()
    lines = [f"- {terms[k]['ar'][0]} → {' / '.join(terms[k][lang])}" for k in present]
    return "Use these approved renderings for religious terms:\n" + "\n".join(lines)


def _instructions(arabic: str, lang: str) -> str:
    parts = [
        f"You translate a live Friday sermon (khutbah) from Arabic into {LANGUAGE_NAMES[lang]}.",
        "The input is a speech-to-text segment and may be an incomplete sentence.",
        "Preserve the religious meaning, tone, names and honorifics.",
        "Do not add explanations, notes, quotation marks or the original Arabic. Return only the translation.",
    ]
    hint = _glossary_hint(arabic, lang)
    if hint:
        parts.append(hint)
    return "\n".join(parts)


def _request(arabic: str, lang: str, with_reasoning: bool):
    kwargs = {"model": translation_model(), "instructions": _instructions(arabic, lang), "input": arabic}
    effort = translation_reasoning_effort()
    if with_reasoning and effort and translation_model().startswith(("gpt-5", "o")):
        kwargs["reasoning"] = {"effort": effort}
    return get_client().responses.create(**kwargs)


def translate_text(text: str, target_language: str) -> tuple[str, list[str]]:
    """Return (translation, glossary_warnings). Raises ValueError / TranslationError."""
    if target_language not in TRANSLATION_LANGUAGES:
        raise ValueError("Supported languages are: en, ur, hi")
    text = (text or "").strip()
    if not text:
        return "", []

    from openai import BadRequestError, OpenAIError

    try:
        try:
            response = _request(text, target_language, with_reasoning=True)
        except BadRequestError as exc:
            # Some models reject the reasoning parameter; retry once without it.
            if "reasoning" not in str(exc).lower():
                raise
            response = _request(text, target_language, with_reasoning=False)
    except AIUnavailable as exc:
        raise TranslationError("AI translation is not configured (OPENAI_API_KEY).") from exc
    except OpenAIError as exc:
        log.error("translation to %s failed: %s", target_language, type(exc).__name__)
        raise TranslationError(str(exc)) from exc

    translated = (response.output_text or "").strip()
    if not translated:
        raise TranslationError("empty translation")
    return translated, check_glossary(text, translated, target_language)
