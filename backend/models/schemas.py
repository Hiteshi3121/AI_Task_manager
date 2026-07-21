"""
Pydantic models define the shape of data moving through the app.
FastAPI uses these to validate incoming requests and serialize outgoing
responses automatically. Every other file imports from here rather than
redefining dicts ad hoc — one source of truth for what a "task" looks like.
"""

from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import Optional


# ---------- Tasks ----------

class TaskCreate(BaseModel):
    raw_text: str


class ClassifiedTask(BaseModel):
    """What the classifier agent returns before it's saved to the DB."""
    title: str
    bucket_id: str
    sub_bucket_id: Optional[str] = None
    person_id: Optional[int] = None
    student_id: Optional[int] = None
    priority: str          # high / medium / low
    due: str                # today / this week / upcoming / no deadline


class Task(BaseModel):
    """A task as stored in and returned from the database."""
    id: UUID
    raw_text: str
    title: str
    bucket_id: str
    sub_bucket_id: Optional[str] = None
    person_id: Optional[int] = None
    student_id: Optional[int] = None
    priority: str
    due: str
    due_date: Optional[datetime] = None  # only set when due == "custom"
    done: bool
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    done: Optional[bool] = None
    title: Optional[str] = None
    priority: Optional[str] = None
    due: Optional[str] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = None  # daily / weekly / monthly / null to clear


# ---------- Students (Ascend Now roster) ----------

class StudentCreate(BaseModel):
    name: str
    current_project: Optional[str] = None
    status: str = "not_started"  # not_started / in_progress / on_hold / completed / cancelled
    next_follow_up: Optional[str] = None


class Student(BaseModel):
    id: int
    name: str
    current_project: Optional[str] = None
    status: str
    next_follow_up: Optional[str] = None
    last_updated: datetime


class StudentUpdate(BaseModel):
    current_project: Optional[str] = None
    status: Optional[str] = None
    next_follow_up: Optional[str] = None


# ---------- Daily brief ----------

class FollowUpItem(BaseModel):
    name: str
    reason: str


class BriefBullet(BaseModel):
    text: str
    priority: str  # high / medium / low — drives the bullet's color in the UI


class DailyBrief(BaseModel):
    what_matters_today: list[BriefBullet]
    who_to_check_on: list[FollowUpItem]
    recent_days: list[dict]   # raw aggregation, no LLM involved


class DailyReport(BaseModel):
    id: int
    report_date: date
    tasks_completed: int
    tasks_carried_over: int
    tasks_by_bucket: dict
    brief_text: Optional[str] = None
    created_at: datetime
