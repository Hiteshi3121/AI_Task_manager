"""
Smart follow-up nudges: finds tasks that have been lingering overdue
for 3+ days so Ishita can't accidentally forget them.
"""

from db.connection import get_connection

NUDGE_THRESHOLD_DAYS = 3


def get_overdue_nudges() -> list[dict]:
    """
    Returns open tasks that are currently overdue AND were created
    more than NUDGE_THRESHOLD_DAYS ago, ordered by how long they've
    been sitting (oldest first). Each row includes a `days_open` field
    so the UI can show "overdue 5 days" etc.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                    id, title, bucket_id, priority, due, created_at,
                    (current_date - created_at::date) as days_open
                from tasks
                where done = false
                  and due = 'overdue'
                  and created_at < now() - interval '%s days'
                order by created_at asc
                """ % NUDGE_THRESHOLD_DAYS
            )
            return [dict(r) for r in cur.fetchall()]
