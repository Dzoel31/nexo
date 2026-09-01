from datetime import datetime, timedelta, timezone
from typing import List

# Master Reminder Intervals (in minutes)
# H-7d (10080), H-3d (4320), H-1d (1440), H-12h (720), H-1h (60), H-30m (30), H-10m (10)
MASTER_REMINDER_INTERVALS: List[int] = [10080, 4320, 1440, 720, 60, 30, 10]

INDONESIAN_DAYS = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

INDONESIAN_MONTHS = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


WIB_TZ = timezone(timedelta(hours=7))


def to_wib(dt: datetime) -> datetime:
    """Converts any datetime (naive or tz-aware) to timezone-aware WIB (UTC+7)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB_TZ)


def format_indonesian_date(dt: datetime) -> str:
    """Formats a datetime object to Indonesian date format in WIB: e.g. 'Rabu, 02 September 2026'."""
    dt_wib = to_wib(dt)
    day_name = INDONESIAN_DAYS.get(dt_wib.weekday(), "")
    month_name = INDONESIAN_MONTHS.get(dt_wib.month, "")
    return f"{day_name}, {dt_wib.day:02d} {month_name} {dt_wib.year}"


def format_time_wib(dt: datetime) -> str:
    """Formats a datetime to HH:MM format in WIB (UTC+7)."""
    dt_wib = to_wib(dt)
    return dt_wib.strftime("%H:%M")


def prune_reminder_intervals(
    start_time: datetime, now_dt: datetime | None = None
) -> List[int]:
    """
    Filters reminder intervals based on lead time (start_time - now).

    Rule: Keep interval X if (start_time - X minutes) > now + 5 minutes.
    Returns: List of valid intervals sorted descending.
    """
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    if now_dt is None:
        now_dt = datetime.now(timezone.utc)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    cutoff_margin = timedelta(minutes=5)
    valid_intervals: List[int] = []

    for interval in MASTER_REMINDER_INTERVALS:
        trigger_time = start_time - timedelta(minutes=interval)
        if trigger_time > (now_dt + cutoff_margin):
            valid_intervals.append(interval)

    valid_intervals.sort(reverse=True)
    return valid_intervals


def get_human_time_label(interval_minutes: int) -> str:
    """Returns human-readable Indonesian time label for reminders."""
    labels = {
        10080: "H-7 Hari",
        4320: "H-3 Hari",
        1440: "H-1 Hari",
        720: "12 Jam Lagi",
        60: "1 Jam Lagi",
        30: "30 Menit Lagi",
        10: "10 Menit Lagi",
    }
    return labels.get(interval_minutes, f"{interval_minutes} Menit Lagi")
