import os
from fastapi import APIRouter, File, HTTPException, UploadFile
from groq import Groq

router = APIRouter()


@router.post("/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        result = client.audio.transcriptions.create(
            file=(file.filename or "audio.webm", audio_bytes, file.content_type or "audio/webm"),
            model="whisper-large-v3",
            language="en",
            prompt=(
                "Udukku, Ishita, Evita, Meezan, Heeral, Evani, Hiya, Sagarika, "
                "Ascend Now, Hyrox, music room, pitch deck, carousel, partnerships, "
                "operations, marketing, content, entrepreneurship, podcast, reel, "
                "Instagram, AI task manager"
            ),
        )
        return {"text": result.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
