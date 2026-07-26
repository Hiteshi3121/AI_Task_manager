import os
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

KEYWORDS = [
    "Udukku", "Ishita", "Evita", "Meezan", "Heeral", "Evani", "Hiya", "Sagarika",
    "Hyrox", "podcast", "carousel", "partnerships", "operations",
    "marketing", "entrepreneurship", "reel", "Instagram",
]

@router.post("/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        api_key = os.getenv("DEEPGRAM_API_KEY")

        # Build URL manually so keywords aren't double-encoded
        keyword_params = "&".join(f"keywords={kw}:2" for kw in KEYWORDS)
        url = f"https://api.deepgram.com/v1/listen?model=nova-2&language=en&punctuate=true&smart_format=true&{keyword_params}"

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": file.content_type or "audio/webm",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, content=audio_bytes)

        print(f"[transcribe] Deepgram status: {response.status_code}")

        if response.status_code != 200:
            print(f"[transcribe] Deepgram error: {response.text}")
            raise HTTPException(status_code=500, detail=f"Deepgram error {response.status_code}: {response.text}")

        data = response.json()
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        print(f"[transcribe] Got transcript: '{transcript}'")
        return {"text": transcript}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[transcribe] Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
