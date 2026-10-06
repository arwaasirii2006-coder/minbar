from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.common import api_error, paid_api_access, require_language
from services.config import TRANSLATION_LANGUAGES
from services.pipeline import build_segment
from services.verse_service import detect_verse

router = APIRouter(tags=["translation"])


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    target_language: str


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


@router.post("/translate", dependencies=[Depends(paid_api_access)])
async def translate(request: TranslationRequest):
    """Arabic text → one language. Quran verses use the verified translation."""
    lang = require_language(request.target_language)
    seg = await build_segment(request.text, [lang])
    if seg is None or seg["is_unclear"]:
        raise api_error(400, "unclear_text", "النص لا يحتوي على كلام عربي واضح.")
    if lang in seg["failed_languages"] and not seg["verse"]:
        raise api_error(502, "translation_failed", "تعذّرت الترجمة الآلية مؤقتًا.")
    return {
        "source_language": "ar",
        "target_language": lang,
        "translation": seg["translations"][lang],
        "verse": seg["verse"],
        "translation_failed": lang in seg["failed_languages"],
        "glossary_warnings": seg["glossary_warnings"].get(lang, []),
    }


@router.post("/detect_verse")
async def detect(request: TextRequest):
    """Quran detection only (no AI): verse reference, Uthmani text and verified translations."""
    return {"verse": await asyncio.to_thread(detect_verse, request.text, TRANSLATION_LANGUAGES)}
