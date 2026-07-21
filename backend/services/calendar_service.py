"""
Handles storing/retrieving Google OAuth tokens and fetching today's
calendar events. Token refresh is automatic — callers just call
get_today_events() and get a list back (or [] if not connected).
"""

import os
from datetime import datetime, timezone, timedelta

import requests

from db.connection import get_connection

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_URL = "https://www.googleapis.com/calendar/v3"

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


# ---------------------------------------------------------------------------
# Token storage
# ---------------------------------------------------------------------------

def save_tokens(access_token: str, refresh_token: str | None, expires_in: int) -> None:
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into oauth_tokens (provider, user_label, access_token, refresh_token, token_expiry, updated_at)
                values ('google', 'primary', %s, %s, %s, now())
                on conflict (provider, user_label) do update
                    set access_token  = excluded.access_token,
                        refresh_token = coalesce(excluded.refresh_token, oauth_tokens.refresh_token),
                        token_expiry  = excluded.token_expiry,
                        updated_at    = now()
                """,
                (access_token, refresh_token, expiry),
            )
            conn.commit()


def _load_tokens() -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select * from oauth_tokens where provider = 'google' and user_label = 'primary'"
            )
            return cur.fetchone()


def is_connected() -> bool:
    row = _load_tokens()
    return row is not None


def disconnect() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("delete from oauth_tokens where provider = 'google' and user_label = 'primary'")
            conn.commit()


def _get_valid_access_token() -> str | None:
    row = _load_tokens()
    if not row:
        return None

    # Still valid?
    if row["token_expiry"] and row["token_expiry"] > datetime.now(timezone.utc):
        return row["access_token"]

    # Refresh
    if not row["refresh_token"]:
        return None

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": row["refresh_token"],
        "grant_type": "refresh_token",
    }, timeout=10)

    if not resp.ok:
        return None

    data = resp.json()
    save_tokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),  # Google only re-issues on first auth
        expires_in=data.get("expires_in", 3600),
    )
    return data["access_token"]


# ---------------------------------------------------------------------------
# Calendar fetch
# ---------------------------------------------------------------------------

def get_today_events() -> list[dict]:
    """
    Returns today's calendar events (midnight-to-midnight in local time),
    each as {title, start, end, start_iso, end_iso, all_day}.
    Returns [] if not connected or on any error.
    """
    token = _get_valid_access_token()
    if not token:
        return []

    now = datetime.now(timezone.utc).astimezone()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end   = day_start + timedelta(days=1)

    resp = requests.get(
        f"{GOOGLE_CALENDAR_URL}/calendars/primary/events",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "timeMin": day_start.isoformat(),
            "timeMax": day_end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 20,
        },
        timeout=10,
    )

    if not resp.ok:
        return []

    events = []
    for item in resp.json().get("items", []):
        start_raw = item.get("start", {})
        end_raw   = item.get("end", {})
        all_day   = "date" in start_raw and "dateTime" not in start_raw

        if all_day:
            start_iso = start_raw.get("date", "")
            end_iso   = end_raw.get("date", "")
            start_fmt = start_iso
            end_fmt   = end_iso
        else:
            start_iso = start_raw.get("dateTime", "")
            end_iso   = end_raw.get("dateTime", "")
            # Format: "3:00 PM"
            def _fmt(iso: str) -> str:
                try:
                    dt = datetime.fromisoformat(iso)
                    return dt.strftime("%-I:%M %p") if hasattr(dt, "strftime") else iso
                except Exception:
                    return iso
            start_fmt = _fmt(start_iso)
            end_fmt   = _fmt(end_iso)

        events.append({
            "title":     item.get("summary", "(No title)"),
            "start":     start_fmt,
            "end":       end_fmt,
            "start_iso": start_iso,
            "end_iso":   end_iso,
            "all_day":   all_day,
        })

    return events


# ---------------------------------------------------------------------------
# Event creation
# ---------------------------------------------------------------------------

def create_event(summary: str, start_iso: str, end_iso: str) -> str | None:
    """
    Creates a Google Calendar event and returns the event ID, or None on failure.
    start_iso / end_iso must be full ISO 8601 strings with timezone offset.
    """
    token = _get_valid_access_token()
    if not token:
        return None

    body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end":   {"dateTime": end_iso},
    }

    resp = requests.post(
        f"{GOOGLE_CALENDAR_URL}/calendars/primary/events",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=10,
    )

    if not resp.ok:
        print(f"[calendar_service] create_event failed: {resp.status_code} {resp.text}")
        return None

    return resp.json().get("id")


def delete_event(event_id: str) -> None:
    token = _get_valid_access_token()
    if not token:
        return

    resp = requests.delete(
        f"{GOOGLE_CALENDAR_URL}/calendars/primary/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if not resp.ok and resp.status_code != 410:  # 410 = already deleted, that's fine
        print(f"[calendar_service] delete_event failed: {resp.status_code} {resp.text}")
