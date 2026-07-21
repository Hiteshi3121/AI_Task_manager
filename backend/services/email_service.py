"""
Sends emails via Gmail SMTP.
All config comes from .env — swap credentials to switch accounts.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SENDER    = os.getenv("GMAIL_SENDER")
PASSWORD  = os.getenv("GMAIL_APP_PASSWORD")
RECIPIENT = os.getenv("GMAIL_RECIPIENT")


def send_email(subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECIPIENT, msg.as_string())


def _overdue_nudges_html() -> str:
    from services.nudge_service import get_overdue_nudges
    nudges = get_overdue_nudges()
    if not nudges:
        return ""
    items = "".join(
        f'<li style="margin-bottom:6px;"><b>{n["title"]}</b> — <span style="color:#E24B4A">{n["days_open"]} days overdue</span> ({n["bucket_id"]})</li>'
        for n in nudges
    )
    return f"""
    <div style="background:#fff5f5;border:1px solid #fcc;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
      <h3 style="margin:0 0 12px;font-size:14px;color:#E24B4A;">⚠️ Overdue — needs attention</h3>
      <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.6;">{items}</ul>
    </div>
    """


def send_daily_brief(brief: dict) -> None:
    bullets = brief.get("what_matters_today", [])
    followups = brief.get("who_to_check_on", [])
    events = brief.get("calendar_events", [])

    PRIORITY_COLOR = {"high": "#E24B4A", "medium": "#EF9F27", "low": "#639922"}

    bullets_html = "".join(
        f'<li style="margin-bottom:6px;"><span style="color:{PRIORITY_COLOR.get(b["priority"], "#999")};font-weight:700;">●</span> {b["text"]}</li>'
        for b in bullets
    ) or "<li style='color:#999'>Nothing urgent right now.</li>"

    followups_html = "".join(
        f'<li style="margin-bottom:6px;"><b>{f["name"]}</b> — {f["reason"]}</li>'
        for f in followups
    ) or "<li style='color:#999'>No follow-ups pending.</li>"

    if events:
        events_html = "".join(
            f'<li style="margin-bottom:6px;"><b>{e["title"]}</b> — {"All day" if e["all_day"] else e["start"] + " – " + e["end"]}</li>'
            for e in events
        )
    else:
        events_html = "<li style='color:#999'>No events today.</li>"

    from datetime import date
    today = date.today().strftime("%A, %d %B %Y")

    overdue_section = _overdue_nudges_html()

    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#222;">
      <div style="margin-bottom:20px;">
        <h2 style="margin:0;font-size:20px;">Ishita HQ — Daily Brief</h2>
        <p style="margin:4px 0 0;color:#777;font-size:13px;">{today}</p>
      </div>

      {overdue_section}

      <div style="background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
        <h3 style="margin:0 0 12px;font-size:14px;">💡 What matters today</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.6;">
          {bullets_html}
        </ul>
      </div>

      <div style="background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:16px 20px;margin-bottom:16px;">
        <h3 style="margin:0 0 12px;font-size:14px;">📅 Today's calendar</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.6;">
          {events_html}
        </ul>
      </div>

      <div style="background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:16px 20px;">
        <h3 style="margin:0 0 12px;font-size:14px;">👥 Who to check on today</h3>
        <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.6;">
          {followups_html}
        </ul>
      </div>

      <p style="margin-top:20px;font-size:11px;color:#bbb;text-align:center;">Ishita HQ · sent automatically every morning</p>
    </div>
    """

    send_email(f"Daily Brief — {today}", html)


def send_event_reminder(event_title: str, start_time: str) -> None:
    today = __import__("datetime").date.today().strftime("%A, %d %B")
    html = f"""
    <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#222;">
      <div style="background:#fff;border:1px solid #e5e5e5;border-radius:12px;padding:16px 20px;">
        <h3 style="margin:0 0 8px;font-size:15px;">⏰ Starting in 30 minutes</h3>
        <p style="margin:0;font-size:14px;font-weight:600;">{event_title}</p>
        <p style="margin:4px 0 0;font-size:13px;color:#777;">{today} at {start_time}</p>
      </div>
    </div>
    """
    send_email(f"Reminder: {event_title} at {start_time}", html)
