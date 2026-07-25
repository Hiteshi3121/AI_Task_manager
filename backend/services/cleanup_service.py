"""
Rolling data window: keeps the DB under the Neon free-tier 512 MB limit.

Rules (applied in order, oldest first):
  1. Completed tasks older than 90 days  → deleted
  2. daily_reports rows older than 90 days → deleted

Triggered automatically on every new task creation so no cron job is needed.
Only runs if the last cleanup was >24 hours ago (tracked in-process) to avoid
running the DELETE queries on every single request.
"""

from datetime import datetime, timedelta
from db.connection import get_connection

WINDOW_DAYS = 90          # rolling window size
_last_run: datetime | None = None


def maybe_cleanup() -> None:
    global _last_run
    now = datetime.utcnow()

    # Throttle: at most once per 24 hours
    if _last_run and (now - _last_run) < timedelta(hours=24):
        return

    _last_run = now
    _run_cleanup()


def _run_cleanup() -> None:
    cutoff = datetime.utcnow() - timedelta(days=WINDOW_DAYS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Delete old completed tasks
            cur.execute(
                "DELETE FROM tasks WHERE done = true AND completed_at < %s",
                (cutoff,),
            )
            tasks_deleted = cur.rowcount

            # Delete old daily reports
            cur.execute(
                "DELETE FROM daily_reports WHERE report_date < %s",
                (cutoff.date(),),
            )
            reports_deleted = cur.rowcount

            conn.commit()

    if tasks_deleted or reports_deleted:
        print(
            f"[cleanup] removed {tasks_deleted} completed tasks "
            f"and {reports_deleted} daily reports older than {WINDOW_DAYS} days"
        )
