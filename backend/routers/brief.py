from fastapi import APIRouter, HTTPException
from services import brief_service
from services.email_service import send_daily_brief

router = APIRouter()


@router.get("/")
async def get_brief():
    brief_service.archive_today_if_missing()
    return brief_service.get_daily_brief()


@router.post("/send-email")
async def send_brief_email():
    try:
        brief_service.archive_today_if_missing()
        brief = brief_service.get_daily_brief()
        send_daily_brief(brief)
        return {"sent": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
