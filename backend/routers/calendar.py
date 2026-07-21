import os
import urllib.parse

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from services import calendar_service

router = APIRouter()

CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/calendar/oauth/callback")
SCOPES        = "https://www.googleapis.com/auth/calendar.events"
FRONTEND_URL  = os.getenv("CORS_ORIGIN", "http://localhost:5173")


@router.get("/authorize")
async def authorize():
    """Redirect the browser to Google's OAuth consent page."""
    params = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",   # so we get a refresh token
        "prompt":        "consent",   # force refresh token even if previously authorized
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@router.get("/oauth/callback")
async def oauth_callback(code: str | None = None, error: str | None = None):
    """Google redirects here after user grants/denies consent."""
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}?calendar=error")

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code":          code,
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri":  REDIRECT_URI,
            "grant_type":    "authorization_code",
        },
        timeout=10,
    )

    if not resp.ok:
        return RedirectResponse(f"{FRONTEND_URL}?calendar=error")

    data = resp.json()
    calendar_service.save_tokens(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in", 3600),
    )

    return RedirectResponse(f"{FRONTEND_URL}?calendar=connected")


@router.get("/status")
async def status():
    return {"connected": calendar_service.is_connected()}


@router.delete("/disconnect")
async def disconnect():
    calendar_service.disconnect()
    return {"disconnected": True}


@router.get("/events/today")
async def today_events():
    return calendar_service.get_today_events()
