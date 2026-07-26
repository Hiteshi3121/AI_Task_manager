import os
import asyncio
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

BASE = "https://api.assemblyai.com/v2"

WORD_BOOST = [
    "Udukku", "Ishita", "Evita", "Meezan", "Heeral", "Evani", "Hiya", "Sagarika",
    "Ascend Now", "Hyrox", "pitch deck", "carousel", "partnerships", "operations",
    "marketing", "entrepreneurship", "podcast", "reel", "Instagram", "music room",
]


@router.post("/")
async def transcribe_audio(file: UploadFile = File(...)):
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    headers = {"authorization": api_key}

    try:
        audio_bytes = await file.read()

        async with httpx.AsyncClient(timeout=60) as client:

            # Step 1 — upload audio
            upload_res = await client.post(
                f"{BASE}/upload",
                headers={**headers, "content-type": "application/octet-stream"},
                content=audio_bytes,
            )
            upload_res.raise_for_status()
            audio_url = upload_res.json()["upload_url"]

            # Step 2 — request transcription
            transcript_res = await client.post(
                f"{BASE}/transcript",
                headers=headers,
                json={
                    "audio_url": audio_url,
                    "language_code": "en",
                    "word_boost": WORD_BOOST,
                    "boost_param": "high",
                },
            )
            transcript_res.raise_for_status()
            transcript_id = transcript_res.json()["id"]

            # Step 3 — poll until done
            for _ in range(30):
                await asyncio.sleep(1)
                poll_res = await client.get(
                    f"{BASE}/transcript/{transcript_id}",
                    headers=headers,
                )
                poll_res.raise_for_status()
                data = poll_res.json()

                if data["status"] == "completed":
                    return {"text": data.get("text", "")}
                if data["status"] == "error":
                    raise HTTPException(status_code=500, detail=f"AssemblyAI error: {data.get('error')}")

        raise HTTPException(status_code=500, detail="Transcription timed out")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
