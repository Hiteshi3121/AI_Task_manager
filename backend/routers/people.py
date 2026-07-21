from fastapi import APIRouter
from services import people_service

router = APIRouter()


@router.get("/")
async def list_all():
    return people_service.list_people_with_tasks()
