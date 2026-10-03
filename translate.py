from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found in .env")

client = OpenAI(api_key=api_key)


class TranslationRequest(BaseModel):
    text: str
    target_language: str


LANGUAGES = {
    "en": "English",
    "ur": "Urdu",
    "hi": "Hindi"
}


@router.post("/translate")
async def translate_text(request: TranslationRequest):
    try:
        if request.target_language not in LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail="Supported languages are: en, ur, hi"
            )

        target_language = LANGUAGES[request.target_language]

        response = client.responses.create(
            model="gpt-5-mini",
            instructions=(
                "Translate the Arabic text accurately into the requested language. "
                "Preserve the meaning and return only the translation."
            ),
            input=f"Translate this Arabic text into {target_language}: {request.text}"
        )

        return {
            "source_language": "ar",
            "target_language": request.target_language,
            "translation": response.output_text
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )