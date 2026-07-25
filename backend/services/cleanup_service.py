"""
Rolling data window: keeps the DB under the Neon free-tier 512 MB limit.

Two triggers (either one fires cleanup):
  1. PRIMARY  — DB size exceeds SIZE_WARN_MB (450 MB = 88% of 512 MB limit)
               → delete oldest completed tasks in batches until size drops
                 below SIZE_TARGET_MB (400 MB), then delete old daily_reports
  2. FALLBACK — completed tasks or daily_reports older than FALLBACK_DAYS (90)
               → always cleans up regardless of current size

Triggered on every new task creation. Throttled to once per 24 h to avoid
running the size query on every request.
"""

from datetime import datetime, timedelta
from db.connection import get_connection

SIZE_WARN_MB   = 450    # start cleaning when DB reaches this
SIZE_TARGET_MB = 400    # keep deleting until DB is back below this
FALLBACK_DAYS  = 90     # also delete anything older than this regardless of size
BATCH_SIZE     = 200    # rows deleted per iteration when size-triggered

_last_run: datetime | None = None


def maybe_cleanup() -> None:
    global _last_run
    now = datetime.utcnow()
    if _last_run and (now - _last_run) < timedelta(hours=24):
        return
    _last_run = now
    _run_cleanup()


def _db_size_mb() -> float:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_database_size(current_database()) AS size")
            row = cur.fetchone()
            return row["size"] / (1024 * 1024)


def _run_cleanup() -> None:
    size_mb = _db_size_mb()
    print(f"[cleanup] DB size: {size_mb:.1f} MB")

    total_tasks_deleted = 0
    total_reports_deleted = 0

    # PRIMARY: size-based — delete oldest completed tasks in batches until safe
    if size_mb >= SIZE_WARN_MB:
        print(f"[cleanup] size {size_mb:.1f} MB >= {SIZE_WARN_MB} MB threshold — purging oldest completed tasks")
        while True:
            current_mb = _db_size_mb()
            if current_mb < SIZE_TARGET_MB:
                break
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM tasks
                        WHERE id IN (
                            SELECT id FROM tasks
                            WHERE done = true
                            ORDER BY completed_at ASC NULLS FIRST
                            LIMIT %s
                        )
                        """,
                        (BATCH_SIZE,),
                    )
                    deleted = cur.rowcount
                    conn.commit()
            if deleted == 0:
                break  # nothing left to delete
            total_tasks_deleted += deleted

    # FALLBACK: time-based — always prune anything older than FALLBACK_DAYS
    cutoff = datetime.utcnow() - timedelta(days=FALLBACK_DAYS)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tasks WHERE done = true AND completed_at < %s",
                (cutoff,),
            )
            total_tasks_deleted += cur.rowcount

            cur.execute(
                "DELETE FROM daily_reports WHERE report_date < %s",
                (cutoff.date(),),
            )
            total_reports_deleted += cur.rowcount

            conn.commit()

    if total_tasks_deleted or total_reports_deleted:
        final_mb = _db_size_mb()
        print(
            f"[cleanup] removed {total_tasks_deleted} completed tasks, "
            f"{total_reports_deleted} daily_reports — DB now {final_mb:.1f} MB"
        )
