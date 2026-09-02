import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """Helper to initialize Google Calendar API client."""
    sa_file = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json"
    )
    cal_id = os.environ.get("GOOGLE_CALENDAR_ID")

    if not sa_file or not os.path.exists(sa_file):
        raise FileNotFoundError(
            f"Google Service Account file not found or not configured: {sa_file}"
        )
    if not cal_id:
        raise ValueError("GOOGLE_CALENDAR_ID environment variable is missing.")

    creds = service_account.Credentials.from_service_account_file(
        sa_file, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds), cal_id


async def create_gcal_event(
    name: str,
    description: str,
    start_dt: datetime,
    end_dt: datetime,
    location: str = "",
) -> Optional[Dict[str, Any]]:
    """Create Google Calendar event asynchronously via background thread."""

    def _sync_create():
        service, cal_id = _get_service()
        event_body = {
            "summary": name,
            "description": description,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Asia/Jakarta",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Jakarta",
            },
            "location": location,
        }
        return service.events().insert(calendarId=cal_id, body=event_body).execute()

    try:
        return await asyncio.to_thread(_sync_create)
    except Exception as e:
        logger.error(f"Error creating Google Calendar event: {e}")
        return None


async def delete_gcal_event(event_id: str) -> bool:
    """Delete Google Calendar event asynchronously via background thread."""

    def _sync_delete():
        service, cal_id = _get_service()
        service.events().delete(calendarId=cal_id, eventId=event_id).execute()
        return True

    try:
        await asyncio.to_thread(_sync_delete)
        return True
    except Exception as e:
        logger.error(f"Error deleting Google Calendar event ({event_id}): {e}")
        return False


async def list_gcal_events(
    time_min: Optional[datetime] = None, max_results: int = 15
) -> List[Dict[str, Any]]:
    """List Google Calendar events asynchronously via background thread."""

    def _sync_list():
        service, cal_id = _get_service()
        t_min = (time_min or datetime.now(timezone.utc)).isoformat()
        events_result = (
            service.events()
            .list(
                calendarId=cal_id,
                timeMin=t_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    try:
        return await asyncio.to_thread(_sync_list)
    except Exception as e:
        logger.error(f"Error listing Google Calendar events: {e}")
        return []
