from fastapi import APIRouter, HTTPException
from models.schemas import StudentCreate, StudentUpdate
from services import student_service

router = APIRouter()


@router.get("/")
async def list_all(status: str | None = None):
    return student_service.list_students(status=status)


@router.post("/")
async def create(payload: StudentCreate):
    return student_service.create_student(
        payload.name, payload.current_project, payload.status, payload.next_follow_up
    )


@router.patch("/{student_id}")
async def update(student_id: int, payload: StudentUpdate):
    updates = payload.model_dump(exclude_none=True)
    result = student_service.update_student(student_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Student not found")
    return result


@router.delete("/{student_id}")
async def delete(student_id: int):
    student_service.delete_student(student_id)
    return {"deleted": student_id}


@router.get("/{student_id}/tasks")
async def student_tasks(student_id: int):
    return student_service.get_tasks_for_student(student_id)
