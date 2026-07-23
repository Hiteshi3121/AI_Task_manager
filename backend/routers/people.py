from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import people_service

router = APIRouter()

class PersonCreate(BaseModel):
    name: str
    role: str = ''

@router.get("/")
async def list_all():
    return people_service.list_people_with_tasks()

@router.post("/")
async def add_person(body: PersonCreate):
    return people_service.create_person(body.name.strip(), body.role.strip())

@router.delete("/{person_id}")
async def remove_person(person_id: int):
    ok = people_service.delete_person(person_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"ok": True}
