from datetime import UTC, datetime, timedelta
from typing import Any


def event_expiry_time(start_time: datetime, end_time: datetime | None) -> datetime:
    """Return the persisted event end time, defaulting to a two-hour duration."""
    return end_time or (start_time + timedelta(hours=2))


def parse_calendar_times(
    item: dict[str, Any],
) -> tuple[datetime, datetime, bool] | None:
    """Parse Google Calendar start/end values into timezone-aware datetimes."""
    start_obj = item.get("start", {})
    end_obj = item.get("end", {})
    is_all_day = "date" in start_obj and "dateTime" not in start_obj
    start_iso = start_obj.get("dateTime") or start_obj.get("date")
    end_iso = end_obj.get("dateTime") or end_obj.get("date")
    if not start_iso:
        return None

    start_dt = datetime.fromisoformat(start_iso)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=UTC)

    end_dt = (
        datetime.fromisoformat(end_iso) if end_iso else start_dt + timedelta(hours=2)
    )
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=UTC)
    return start_dt, end_dt, is_all_day
