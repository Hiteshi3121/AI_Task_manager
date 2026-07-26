import os
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"

KEYWORDS = [
    "Udukku", "Ishita", "Evita", "Meezan", "Heeral", "Evani", "Hiya", "Sagarika",
    "Ascend Now", "Hyrox", "podcast", "carousel", "partnerships", "operations",
    "marketing", "entrepreneurship", "reel", "Instagram", "pitch deck",
]


@router.post("/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        api_key = os.getenv("DEEPGRAM_API_KEY")

        params = {
            "model": "nova-2",
            "language": "en",
            "punctuate": "true",
            "smart_format": "true",
            "keywords": [f"{kw}:2" for kw in KEYWORDS],
        }

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": file.content_type or "audio/webm",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                DEEPGRAM_API_URL,
                params=params,
                headers=headers,
                content=audio_bytes,
            )
            response.raise_for_status()

        transcript = (
            response.json()
            ["results"]["channels"][0]["alternatives"][0]["transcript"]
        )
        return {"text": transcript}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
