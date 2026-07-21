"""
Brief service: builds the full daily brief shown on the dashboard.
Does the counting itself (no LLM, no risk of wrong numbers), then asks
brief_agent for just the narrative and follow-up phrasing.
"""

import json
from datetime import date, timedelta
from db.connection import get_connection
from agents.brief_agent import generate_brief_narrative
from services import task_service
from services import calendar_service

# Catching the broad Exception here is deliberate: the LLM provider can fail
# in many distinct ways (rate limit, network timeout, auth error, malformed
# response), and the dashboard should degrade gracefully in every case
# rather than crash. We log the real error so it's still visible in the
# terminal for debugging, just not surfaced as a 500 to the user.


def _get_open_tasks() -> list[dict]:
    # Routed through task_service so the same due-staleness resync that
    # runs for the boards (see due_utils.py) also runs before the brief's
    # own SQL aggregations below — otherwise this query could see a "today"
    # label that's actually three days old.
    return task_service.list_tasks(done=False)


def _get_overdue_candidates() -> list[dict]:
    """
    Plain-rule candidates for 'who to check on': high/medium priority,
    due today/this week/already overdue, tied to a person or student, not
    yet done. The LLM only rephrases these — it doesn't decide who's on
    the list. Must run after _get_open_tasks() in the same request so the
    due-staleness resync has already happened.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select t.title, t.priority, t.due,
                       coalesce(p.name, s.name) as name
                from tasks t
                left join people p on t.person_id = p.id
                left join students s on t.student_id = s.id
                where t.done = false
                  and t.due in ('today', 'this week', 'overdue')
                  and t.priority in ('high', 'medium')
                  and (t.person_id is not null or t.student_id is not null)
                order by t.priority desc
                """
            )
            return cur.fetchall()


def _get_recent_days(n: int = 7) -> list[dict]:
    """Pure aggregation, no LLM — pulled straight from the daily_reports archive."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select report_date, tasks_completed, tasks_carried_over
                from daily_reports
                order by report_date desc
                limit %s
                """,
                (n,),
            )
            return cur.fetchall()


def get_daily_brief() -> dict:
    open_tasks = _get_open_tasks()
    overdue_candidates = _get_overdue_candidates()
    recent_days = _get_recent_days()

    # Fetch calendar events if connected — errors are swallowed so a
    # Calendar outage never breaks the brief.
    try:
        calendar_events = calendar_service.get_today_events()
    except Exception:
        calendar_events = []

    try:
        narrative = generate_brief_narrative(open_tasks, overdue_candidates, calendar_events)
    except json.JSONDecodeError:
        # Model returned text that wasn't valid JSON
        narrative = {
            "what_matters_today": [
                {"text": "Couldn't generate today's summary — check open tasks manually.", "priority": "medium"}
            ],
            "who_to_check_on": [],
        }
    except Exception as e:
        # Catches rate limits (429), network errors, auth failures, etc.
        # Print so it's visible in the terminal for debugging, but never
        # let the dashboard itself crash because of an LLM provider issue.
        print(f"[brief_service] LLM call failed: {e}")
        narrative = {
            "what_matters_today": [
                {"text": "AI summary is temporarily unavailable (provider error or rate limit) — your tasks below are still accurate.", "priority": "medium"}
            ],
            "who_to_check_on": [],
        }

    return {
        "what_matters_today": narrative.get("what_matters_today", []),
        "who_to_check_on": narrative.get("who_to_check_on", []),
        "recent_days": recent_days,
        "calendar_events": calendar_events,
    }


def archive_day_if_missing(report_date: date):
    """
    Writes a row into daily_reports for report_date if it doesn't already
    exist. Used two ways: on-demand for *today* (called from the brief
    endpoint, so today's running totals show up immediately), and on a
    schedule for *yesterday* (called from main.py's background loop, so a
    day's history is never lost even if nobody opened the dashboard that
    day — see archive_yesterday_if_missing below).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("select 1 from daily_reports where report_date = %s", (report_date,))
            if cur.fetchone():
                return  # already archived

            cur.execute(
                "select count(*) as n from tasks where done = true and completed_at::date = %s",
                (report_date,),
            )
            completed = cur.fetchone()["n"]

            cur.execute(
                "select count(*) as n from tasks where done = false and created_at::date < %s",
                (report_date,),
            )
            carried_over = cur.fetchone()["n"]

            cur.execute(
                """
                select bucket_id, count(*) as n
                from tasks
                where created_at::date = %s
                group by bucket_id
                """,
                (report_date,),
            )
            by_bucket = {row["bucket_id"]: row["n"] for row in cur.fetchall()}

            cur.execute(
                """
                insert into daily_reports
                    (report_date, tasks_completed, tasks_carried_over, tasks_by_bucket)
                values (%s, %s, %s, %s)
                """,
                (report_date, completed, carried_over, json.dumps(by_bucket)),
            )
            conn.commit()


def archive_today_if_missing():
    """Kept as the existing entry point the brief endpoint calls on every request."""
    archive_day_if_missing(date.today())


def archive_yesterday_if_missing():
    """
    Called periodically from main.py's background loop (not just on
    demand) so a day's history survives even if the dashboard is never
    opened that day — as long as the backend process is running at some
    point after midnight. This is a stopgap for Phase 1; a real cron/
    scheduled job belongs in Phase 4 once this is deployed.
    """
    archive_day_if_missing(date.today() - timedelta(days=1))