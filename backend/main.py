import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
DAILY_BRIEF_HOUR = 8   # 8 AM IST
REMINDER_MINUTES = 30  # remind 30 min before event

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import brief, students, people, calendar, analytics
from routers import tasks
from services.brief_service import archive_yesterday_if_missing, get_daily_brief
from services import email_service, calendar_service

ARCHIVE_CHECK_INTERVAL_SECONDS = 60 * 60  # hourly is frequent enough — this
# is just a safety net so a day's history survives even if nobody opens the
# dashboard that day; archive_day_if_missing() is a no-op once a date is
# already archived, so running it hourly costs one cheap SELECT per check.


async def _archive_loop():
    while True:
        try:
            archive_yesterday_if_missing()
        except Exception as e:
            print(f"[main] background archive check failed: {e}")
        await asyncio.sleep(ARCHIVE_CHECK_INTERVAL_SECONDS)


async def _daily_brief_email_loop():
    """Sends the daily brief email at 8 AM IST every day."""
    sent_today = None
    while True:
        try:
            now = datetime.now(IST)
            if now.hour == DAILY_BRIEF_HOUR and sent_today != now.date():
                brief = get_daily_brief()
                email_service.send_daily_brief(brief)
                sent_today = now.date()
                print(f"[main] daily brief email sent for {now.date()}")
        except Exception as e:
            print(f"[main] daily brief email failed: {e}")
        await asyncio.sleep(60)  # check every minute


async def _event_reminder_loop():
    """Sends a 30-minute reminder email before each Google Calendar event."""
    reminded = set()  # tracks event ids already reminded today so we don't double-send
    last_reset = None
    while True:
        try:
            now = datetime.now(IST)
            # Reset the reminded set at midnight so next-day events work
            if last_reset != now.date():
                reminded.clear()
                last_reset = now.date()

            if calendar_service.is_connected():
                events = calendar_service.get_today_events()
                for ev in events:
                    if ev.get("all_day") or ev["title"] in reminded:
                        continue
                    try:
                        start = datetime.fromisoformat(ev["start_iso"])
                        if not start.tzinfo:
                            start = start.replace(tzinfo=IST)
                        diff = (start - now).total_seconds() / 60
                        if 0 <= diff <= REMINDER_MINUTES:
                            email_service.send_event_reminder(ev["title"], ev["start"])
                            reminded.add(ev["title"])
                            print(f"[main] reminder sent for: {ev['title']}")
                    except Exception:
                        pass
        except Exception as e:
            print(f"[main] event reminder check failed: {e}")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(_archive_loop()),
        asyncio.create_task(_daily_brief_email_loop()),
        asyncio.create_task(_event_reminder_loop()),
    ]
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(title="Ishita HQ", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(brief.router, prefix="/api/brief", tags=["brief"])
app.include_router(people.router, prefix="/api/people", tags=["people"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.get("/health")
async def health():
    return {"status": "ok"}
