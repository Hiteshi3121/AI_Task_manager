"""
Task service: the only place that writes/reads the `tasks` table.
Routers call into this; this calls into the database. Routers should
never run raw SQL themselves — that's what makes this layer worth having.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from db.connection import get_connection
from agents.classifier_agent import classify_task
from services.due_utils import effective_due
from services import calendar_service

VALID_DUE_VALUES = {"today", "this week", "upcoming", "no deadline"}
IST = ZoneInfo("Asia/Kolkata")


def _sanitize_calendar_event(cal_event: dict) -> dict | None:
    """
    Validates the LLM-returned calendar event datetimes and ensures end_iso
    is always start + 1 hour if missing or malformed.
    Returns None if start_iso is unparseable so we skip the calendar call.
    """
    try:
        start = datetime.fromisoformat(cal_event["start_iso"])
        if not start.tzinfo:
            start = start.replace(tzinfo=IST)
        end = start + timedelta(hours=1)
        return {
            "summary": cal_event.get("summary", ""),
            "start_iso": start.isoformat(),
            "end_iso": end.isoformat(),
        }
    except Exception as e:
        print(f"[task_service] bad calendar_event from LLM, skipping: {e}")
        return None


def _clamp_due(due: str) -> str:
    """
    The classifier is instructed to only return one of VALID_DUE_VALUES, but
    LLMs occasionally drift (e.g. "tomorrow" instead of "today"). Falling
    back to "upcoming" here means a classification quirk surfaces as a
    slightly-off due label instead of a 500 on the DB's check constraint.
    """
    return due if due in VALID_DUE_VALUES else "upcoming"


def _get_known_students() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select name from students where status = 'active'")
            return [row["name"] for row in cur.fetchall()]


def _resolve_person_id(name: str | None) -> int | None:
    if not name:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select id from people where name = %s", (name,))
            row = cur.fetchone()
            return row["id"] if row else None


def _resolve_student_id(name: str | None) -> int | None:
    if not name:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select id from students where name = %s", (name,))
            row = cur.fetchone()
            return row["id"] if row else None


def create_task(raw_text: str) -> dict:
    """
    Full pipeline: classify the raw text, resolve any mentioned person/
    student into a real foreign key, insert the row, return it.
    """
    known_students = _get_known_students()
    classified = classify_task(raw_text, known_students)

    person_id = _resolve_person_id(classified.get("person_name"))
    student_id = _resolve_student_id(classified.get("student_name"))

    # Create Google Calendar event if the classifier detected one and calendar is connected
    cal_event = classified.get("calendar_event")
    calendar_event_id = None
    if cal_event and isinstance(cal_event, dict) and calendar_service.is_connected():
        cal_event = _sanitize_calendar_event(cal_event)
        if cal_event:
            try:
                calendar_event_id = calendar_service.create_event(
                    summary=cal_event.get("summary", classified["title"]),
                    start_iso=cal_event["start_iso"],
                    end_iso=cal_event["end_iso"],
                )
            except Exception as e:
                print(f"[task_service] calendar event creation failed: {e}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into tasks
                    (raw_text, title, bucket_id, sub_bucket_id, person_id,
                     student_id, priority, due, calendar_event_id)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                returning *
                """,
                (
                    raw_text,
                    classified["title"],
                    classified["bucket_id"],
                    classified.get("sub_bucket_id"),
                    person_id,
                    student_id,
                    classified["priority"],
                    _clamp_due(classified["due"]),
                    calendar_event_id,
                ),
            )
            conn.commit()
            return cur.fetchone()


def create_person_task(raw_text: str, person_id: int) -> dict:
    """Classify raw text for title/priority/due via AI, then force bucket=udukku and set person_id."""
    known_students = _get_known_students()
    classified = classify_task(raw_text, known_students)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into tasks
                    (raw_text, title, bucket_id, sub_bucket_id, person_id, priority, due)
                values (%s, %s, 'udukku', %s, %s, %s, %s)
                returning *
                """,
                (
                    raw_text,
                    classified["title"],
                    classified.get("sub_bucket_id"),
                    person_id,
                    classified["priority"],
                    _clamp_due(classified["due"]),
                ),
            )
            conn.commit()
            return cur.fetchone()


def create_manual_task(bucket_id: str, title: str, person_id: int | None = None, student_id: int | None = None) -> dict:
    """Insert a task directly into a bucket without AI classification."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into tasks (raw_text, title, bucket_id, person_id, student_id, priority, due)
                values (%s, %s, %s, %s, %s, 'medium', 'upcoming')
                returning *
                """,
                (title, title, bucket_id, person_id, student_id),
            )
            conn.commit()
            return cur.fetchone()


def _resync_stale_due(rows: list[dict]) -> None:
    """
    Recomputes due for open tasks and persists any change to "overdue" so
    every reader (board, brief SQL aggregations) sees the same value —
    this mutates `rows` in place and writes the changed ones back to disk.
    """
    stale = [
        row for row in rows
        if not row["done"] and effective_due(row["due"], row["created_at"], row.get("due_date")) != row["due"]
    ]
    if not stale:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in stale:
                new_due = effective_due(row["due"], row["created_at"], row.get("due_date"))
                cur.execute("update tasks set due = %s where id = %s", (new_due, row["id"]))
                row["due"] = new_due
            conn.commit()


def list_completed_tasks(days: int = 7) -> list[dict]:
    """Returns tasks completed within the last N days, newest first."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select * from tasks
                where done = true
                  and completed_at >= now() - (%s || ' days')::interval
                order by completed_at desc
                """,
                (str(days),),
            )
            return cur.fetchall()


def list_tasks(bucket_id: str | None = None, done: bool | None = None) -> list[dict]:
    query = "select * from tasks"
    conditions = []
    params = []

    if bucket_id is not None:
        conditions.append("bucket_id = %s")
        params.append(bucket_id)
    if done is not None:
        conditions.append("done = %s")
        params.append(done)

    if conditions:
        query += " where " + " and ".join(conditions)
    query += " order by created_at desc"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    _resync_stale_due(rows)
    return rows


RECURRENCE_DUE = {
    "daily":   "today",
    "weekly":  "this week",
    "monthly": "upcoming",
}


def _spawn_next_recurrence(task: dict) -> None:
    """Creates the next instance of a recurring task after the current one is completed."""
    recurrence = task.get("recurrence")
    if not recurrence:
        return
    next_due = RECURRENCE_DUE.get(recurrence, "upcoming")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into tasks
                    (raw_text, title, bucket_id, sub_bucket_id, person_id,
                     student_id, priority, due, recurrence)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    task["raw_text"], task["title"], task["bucket_id"],
                    task.get("sub_bucket_id"), task.get("person_id"),
                    task.get("student_id"), task["priority"],
                    next_due, recurrence,
                ),
            )
            conn.commit()


def update_task(task_id: str, updates: dict) -> dict | None:
    if not updates:
        return None

    # Switching off "custom" should clear the now-irrelevant exact date —
    # otherwise a stale due_date lingers and effective_due() would keep
    # reasoning about it even though the label no longer says "custom".
    if updates.get("due") not in (None, "custom") and "due_date" not in updates:
        updates = {**updates, "due_date": None}

    # Allow explicitly clearing recurrence by passing recurrence=None —
    # but exclude_none in the router would strip it, so we handle the
    # "clear recurrence" case via a sentinel before the router strips it.
    set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
    params = list(updates.values()) + [task_id]

    # If marking done, also stamp completed_at
    if updates.get("done") is True:
        set_clause += ", completed_at = now()"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"update tasks set {set_clause} where id = %s returning *",
                params,
            )
            conn.commit()
            result = cur.fetchone()

    # Spawn next instance after the DB write commits
    if result and updates.get("done") is True:
        _spawn_next_recurrence(result)

    return result


def delete_task(task_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fetch the calendar_event_id before deleting so we can clean up Google Calendar
            cur.execute("select calendar_event_id from tasks where id = %s", (task_id,))
            row = cur.fetchone()
            cur.execute("delete from tasks where id = %s", (task_id,))
            conn.commit()

    if row and row.get("calendar_event_id") and calendar_service.is_connected():
        try:
            calendar_service.delete_event(row["calendar_event_id"])
        except Exception as e:
            print(f"[task_service] calendar event deletion failed: {e}")
