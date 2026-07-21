"""
"due" is stored as a relative label ("today", "this week", ...), not an
absolute date — so a task labeled "today" at creation still says "today"
three days later unless something recomputes it. This module is that
something: it derives what the label *should* say right now, given when
the task was created, and is called every time tasks are read (not on a
schedule), so it self-heals on the next page load with no background job.
"""

from datetime import date, datetime, timezone

STALE_TO_OVERDUE = {"today", "this week"}


def effective_due(due: str, created_at: datetime, due_date: datetime | None = None) -> str:
    """
    Returns the due label a still-open task should show right now.
    "today" tasks not closed out by the next calendar day, and "this week"
    tasks not closed out by the next ISO week, become "overdue".
    "custom" (an exact picked date/time) becomes "overdue" once that exact
    moment has passed — more precise than the created_at heuristic, since
    we actually know the real deadline. "upcoming" and "no deadline" never
    go stale on their own — there's no fixed point to compare them
    against — and "overdue" stays "overdue".
    """
    if due == "custom":
        if due_date is None:
            return due  # shouldn't happen, but don't crash on bad data
        now = datetime.now(timezone.utc) if due_date.tzinfo else datetime.now()
        return "custom" if due_date >= now else "overdue"

    if due not in STALE_TO_OVERDUE:
        return due

    today = date.today()
    created_date = created_at.date()

    if due == "today":
        return "today" if created_date >= today else "overdue"

    if due == "this week":
        same_week = (
            created_date.isocalendar()[:2] == today.isocalendar()[:2]
        )
        return "this week" if same_week else "overdue"

    return due
