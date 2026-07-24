from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import people_service

router = APIRouter()


class PersonCreate(BaseModel):
    name: str
    role: str = ''


class PersonUpdate(BaseModel):
    name: str | None = None
    role: str | None = None


@router.get("/")
async def list_all():
    return people_service.list_people_with_tasks()


@router.post("/")
async def add_person(body: PersonCreate):
    return people_service.create_person(body.name.strip(), body.role.strip())


@router.patch("/{person_id}")
async def update_person(person_id: int, body: PersonUpdate):
    result = people_service.update_person(
        person_id,
        body.name.strip() if body.name is not None else None,
        body.role.strip() if body.role is not None else None,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Person not found")
    return result


@router.delete("/{person_id}")
async def remove_person(person_id: int):
    ok = people_service.delete_person(person_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Person not found")
    return {"ok": True}
