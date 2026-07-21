from uuid import UUID
from fastapi import APIRouter, HTTPException
from models.schemas import TaskCreate, TaskUpdate
from services import task_service

router = APIRouter()


def _validate_task_id(task_id: str) -> None:
    """Task ids are UUIDs — reject anything else with a clean 400 instead of
    letting a malformed string reach Postgres and raise an unhandled
    InvalidTextRepresentation error (500 with no JSON body)."""
    try:
        UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task id — must be a UUID")


@router.post("/")
async def create(payload: TaskCreate):
    try:
        return task_service.create_task(payload.raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not classify or save task: {e}")


@router.get("/")
async def list_all(bucket_id: str | None = None, done: bool | None = None):
    return task_service.list_tasks(bucket_id=bucket_id, done=done)


@router.patch("/{task_id}")
async def update(task_id: str, payload: TaskUpdate):
    _validate_task_id(task_id)
    updates = payload.model_dump(exclude_none=True)
    # recurrence can be explicitly set to null to clear it — preserve that
    if "recurrence" not in updates and payload.model_fields_set and "recurrence" in payload.model_fields_set:
        updates["recurrence"] = None
    result = task_service.update_task(task_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{task_id}")
async def delete(task_id: str):
    _validate_task_id(task_id)
    task_service.delete_task(task_id)
    return {"deleted": task_id}
