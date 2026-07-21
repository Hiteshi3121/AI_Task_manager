from fastapi import APIRouter
from services import brief_service

router = APIRouter()


@router.get("/")
async def get_brief():
    brief_service.archive_today_if_missing()
    return brief_service.get_daily_brief()
