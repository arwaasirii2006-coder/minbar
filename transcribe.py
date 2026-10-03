from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

router = APIRouter()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found in .env")

client = OpenAI(api_key=api_key)

LANGUAGES = {
    "en": "English",
    "ur": "Urdu",
    "hi": "Hindi"
}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    target_language: str = Form("en")
):
    temp_path = None

    try:
        if target_language not in LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail="Supported languages are: en, ur, hi"
            )

        suffix = os.path.splitext(
            file.filename or "audio.wav"
        )[1] or ".wav"

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name

        # تحويل الصوت العربي إلى نص
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ar"
            )

        arabic_text = transcription.text

        # ترجمة النص إلى اللغة التي اختارها المستخدم
        target_name = LANGUAGES[target_language]

        response = client.responses.create(
            model="gpt-5-mini",
            instructions=(
                f"Translate the Arabic text accurately into {target_name}. "
                "Return only the translated text."
            ),
            input=arabic_text
        )

        translated_text = response.output_text

        return {
            "source_language": "ar",
            "target_language": target_language,
            "original_text": arabic_text,
            "translation": translated_text
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)