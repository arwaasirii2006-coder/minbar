"""Arabic speech-to-text. Audio exists on disk only for the duration of one
OpenAI request and is deleted in all cases."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from fastapi import UploadFile

from services.config import max_upload_bytes, stt_model
from services.openai_client import AIUnavailable, get_client

log = logging.getLogger("minbar")

ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".mp4", ".webm", ".mpeg", ".mpga", ".ogg", ".oga", ".flac"}
_CONTENT_TYPES = {
    "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
    "audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/aac": ".m4a", "video/mp4": ".mp4",
    "audio/webm": ".webm", "video/webm": ".webm",
    "audio/ogg": ".ogg", "audio/flac": ".flac", "audio/x-flac": ".flac",
}
# MediaRecorder blobs smaller than this carry no usable speech.
_MIN_AUDIO_BYTES = 1024


class AudioError(Exception):
    status = 400
    code = "audio_error"


class EmptyAudio(AudioError):
    status = 400
    code = "empty_audio"


class UnsupportedAudio(AudioError):
    status = 415
    code = "unsupported_audio"


class AudioTooLarge(AudioError):
    status = 413
    code = "file_too_large"


class AudioProcessingError(AudioError):
    status = 502
    code = "audio_processing_failed"


class SpeechServiceUnavailable(AudioError):
    status = 503
    code = "ai_unavailable"


async def read_upload(file: UploadFile) -> bytes:
    """Read an upload without ever holding more than the limit in memory."""
    limit = max_upload_bytes()
    data = bytearray()
    while chunk := await file.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > limit:
            raise AudioTooLarge(f"حجم الملف يتجاوز الحد المسموح ({limit // (1024 * 1024)} ميغابايت).")
    return bytes(data)


def audio_suffix(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix in ALLOWED_SUFFIXES:
        return suffix
    base_type = (content_type or "").split(";")[0].strip().lower()
    if base_type in _CONTENT_TYPES:
        return _CONTENT_TYPES[base_type]
    raise UnsupportedAudio("صيغة الملف غير مدعومة. الصيغ المدعومة: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC.")


def validate_audio(data: bytes, filename: str | None, content_type: str | None) -> str:
    suffix = audio_suffix(filename, content_type)
    if len(data) > max_upload_bytes():
        raise AudioTooLarge("حجم الملف يتجاوز الحد المسموح.")
    if len(data) < _MIN_AUDIO_BYTES:
        raise EmptyAudio("المقطع الصوتي فارغ.")
    return suffix


def transcribe_audio(data: bytes, filename: str | None = None, content_type: str | None = None) -> str:
    """Arabic audio → Arabic transcript ('' when no speech was recognised)."""
    suffix = validate_audio(data, filename, content_type)

    from openai import AuthenticationError, BadRequestError, OpenAIError, PermissionDeniedError

    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="minbar-") as f:
            f.write(data)
            path = f.name
        with open(path, "rb") as audio_file:
            result = get_client().audio.transcriptions.create(model=stt_model(), file=audio_file, language="ar")
        return (getattr(result, "text", "") or "").strip()
    except AIUnavailable as exc:
        raise SpeechServiceUnavailable("خدمة التعرف على الكلام غير مُعدّة على الخادم. أضف OPENAI_API_KEY إلى ملف .env ثم أعد تشغيل الخادم.") from exc
    except (AuthenticationError, PermissionDeniedError) as exc:
        log.error("speech-to-text rejected the API key: %s", type(exc).__name__)
        raise SpeechServiceUnavailable("مفتاح OpenAI على الخادم غير صالح أو بلا صلاحية. حدّث OPENAI_API_KEY ثم أعد تشغيل الخادم.") from exc
    except BadRequestError as exc:
        log.warning("speech-to-text rejected audio: %s", exc)
        raise UnsupportedAudio("تعذّر قراءة الملف الصوتي. تأكد أنه ملف صوتي سليم.") from exc
    except OpenAIError as exc:
        log.error("speech-to-text failed: %s", type(exc).__name__)
        raise AudioProcessingError("تعذّرت معالجة الصوت مؤقتًا. ستستمر المحاولة مع المقطع التالي.") from exc
    finally:
        if path and os.path.exists(path):
            os.remove(path)
