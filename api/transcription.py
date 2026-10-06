from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, File, Form, UploadFile

from api.common import audio_error, paid_api_access, require_language
from services.config import TRANSLATION_LANGUAGES
from services.pipeline import build_segment
from services.speech_to_text import AudioError, read_upload, transcribe_audio

router = APIRouter(tags=["transcription"], dependencies=[Depends(paid_api_access)])


async def _transcribe(file: UploadFile) -> str:
    try:
        data = await read_upload(file)
        return await asyncio.to_thread(transcribe_audio, data, file.filename, file.content_type)
    except AudioError as exc:
        raise audio_error(exc)


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...), target_language: str = Form("en")):
    """Arabic audio → Arabic text + translation in one language."""
    require_language(target_language)
    arabic = await _transcribe(file)
    seg = await build_segment(arabic, [target_language])
    seg = seg or {}
    return {
        "source_language": "ar",
        "target_language": target_language,
        "original_text": seg.get("arabic", ""),
        "translation": seg.get("translations", {}).get(target_language, ""),
        "verse": seg.get("verse"),
        "is_unclear": seg.get("is_unclear", False),
        "translation_failed": target_language in seg.get("failed_languages", []),
        "glossary_warnings": seg.get("glossary_warnings", {}).get(target_language, []),
    }


@router.post("/transcribe_all")
async def transcribe_all(file: UploadFile = File(...)):
    """Arabic audio → Arabic text + English, Urdu and Hindi."""
    arabic = await _transcribe(file)
    seg = await build_segment(arabic) or {}
    translations = seg.get("translations", {})
    return {
        "original_text": seg.get("arabic", ""),
        **{lang: translations.get(lang, "") for lang in TRANSLATION_LANGUAGES},
        "translations": translations,
        "verse": seg.get("verse"),
        "is_unclear": seg.get("is_unclear", False),
        "failed_languages": seg.get("failed_languages", []),
        "glossary_warnings": seg.get("glossary_warnings", {}),
    }
