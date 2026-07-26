from fastapi import APIRouter, HTTPException
from services import brief_service, email_service, calendar_service

router = APIRouter()


@router.get("/")
async def get_brief():
    brief_service.archive_today_if_missing()
    return brief_service.get_daily_brief()


@router.post("/test-daily-email")
async def test_daily_email():
    """Send the daily brief email right now — for testing only."""
    try:
        brief = brief_service.get_daily_brief()
        email_service.send_daily_brief(brief)
        return {"sent": True, "to": email_service.RECIPIENT}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-reminder-email")
async def test_reminder_email():
    """Send a test meeting reminder email right now — for testing only."""
    try:
        email_service.send_event_reminder("Test Meeting", "3:00 PM")
        return {"sent": True, "to": email_service.RECIPIENT}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
