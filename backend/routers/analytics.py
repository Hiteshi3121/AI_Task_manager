from fastapi import APIRouter
from db.connection import get_connection
from services import nudge_service

router = APIRouter()


@router.get("/")
async def get_analytics():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Last 30 days from daily_reports
            cur.execute("""
                select report_date, tasks_completed, tasks_carried_over
                from daily_reports
                order by report_date desc
                limit 30
            """)
            daily = cur.fetchall()

            # All-time task counts by bucket
            cur.execute("""
                select bucket_id,
                       count(*) as total,
                       count(*) filter(where done = true) as done,
                       count(*) filter(where done = false) as open
                from tasks
                group by bucket_id
                order by total desc
            """)
            by_bucket = cur.fetchall()

            # Priority breakdown of open tasks
            cur.execute("""
                select priority, count(*) as count
                from tasks
                where done = false
                group by priority
                order by priority
            """)
            by_priority = cur.fetchall()

            # Completion rate this week vs last week
            cur.execute("""
                select
                    count(*) filter(where completed_at >= date_trunc('week', current_date)) as this_week,
                    count(*) filter(where completed_at >= date_trunc('week', current_date) - interval '7 days'
                                     and completed_at < date_trunc('week', current_date)) as last_week
                from tasks
                where done = true
            """)
            weekly = cur.fetchone()

    return {
        "daily": [dict(d) for d in daily],
        "by_bucket": [dict(b) for b in by_bucket],
        "by_priority": [dict(p) for p in by_priority],
        "weekly_completions": dict(weekly) if weekly else {"this_week": 0, "last_week": 0},
        "overdue_nudges": nudge_service.get_overdue_nudges(),
    }
