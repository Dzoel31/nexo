import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import discord

logger = logging.getLogger("event_manager")

# Reminder Interval Profiles (in minutes)
# DEADLINE: H-7d (10080), H-3d (4320), H-1d (1440), 12h (720), 1h (60)
DEADLINE_REMINDER_INTERVALS: List[int] = [10080, 4320, 1440, 720, 60]

# EVENT (Rapat/Acara): H-1d (1440), 1h (60)
EVENT_REMINDER_INTERVALS: List[int] = [1440, 60]

# Master Reminder Intervals for fallback / backward compatibility
MASTER_REMINDER_INTERVALS: List[int] = [10080, 4320, 1440, 720, 60]

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


def detect_event_type(summary: str, is_all_day: bool = False) -> str:
    """
    Detects whether an agenda item is 'DEADLINE' or 'EVENT'.
    Classified as 'DEADLINE' if summary contains '[DL]', '[DEADLINE]', 'DEADLINE', 'BATAS', 'TENGGAT',
    or if is_all_day is True. Otherwise returns 'EVENT'.
    """
    if is_all_day:
        return "DEADLINE"

    text_upper = (summary or "").upper()
    deadline_keywords = [
        "[DL]",
        "[DEADLINE]",
        "DEADLINE",
        "BATAS",
        "TENGGAT",
        "DUE DATE",
        "PENGUMPULAN",
        "SUBMISSION",
    ]
    for kw in deadline_keywords:
        if kw in text_upper:
            return "DEADLINE"

    return "EVENT"


def get_reminder_intervals_for_type(event_type: str = "EVENT") -> List[int]:
    """Returns the interval profile list for a given event type."""
    if event_type == "DEADLINE":
        return list(DEADLINE_REMINDER_INTERVALS)
    return list(EVENT_REMINDER_INTERVALS)


def get_human_time_label(interval_minutes: int) -> str:
    """Returns human-readable Indonesian time label for reminders."""
    labels = {
        10080: "H-7 Hari",
        4320: "H-3 Hari",
        1440: "H-1 Hari",
        720: "12 Jam Lagi",
        60: "1 Jam Lagi",
    }
    return labels.get(interval_minutes, f"{interval_minutes} Menit Lagi")


def prune_reminder_intervals(
    start_time: datetime,
    now_dt: Optional[datetime] = None,
    event_type: str = "EVENT",
) -> List[int]:
    """
    Filters reminder intervals based on lead time (start_time - now) and event type.
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

    target_intervals = get_reminder_intervals_for_type(event_type)

    for interval in target_intervals:
        trigger_time = start_time - timedelta(minutes=interval)
        if trigger_time > (now_dt + cutoff_margin):
            valid_intervals.append(interval)

    valid_intervals.sort(reverse=True)
    return valid_intervals


def build_reminder_embed(
    event_name: str,
    description: Optional[str],
    start_dt: datetime,
    location: str,
    interval_minutes: int,
    event_type: str = "EVENT",
    event_url: Optional[str] = None,
) -> discord.Embed:
    """
    Builds a Discord Embed differentiating visual style and colors
    between 'EVENT' (Blue/Emerald theme) and 'DEADLINE' (Red/Amber warning theme.
    """
    dt_wib = to_wib(start_dt)
    time_label = get_human_time_label(interval_minutes)
    formatted_date = format_indonesian_date(start_dt)
    formatted_time = format_time_wib(start_dt)

    if event_type == "DEADLINE":
        title = f"⏳ Deadline: {event_name}"
        color = 0xEF4444  # Crimson Red
        embed = discord.Embed(
            title=title,
            description=description
            or "Halo teman-teman, jangan lupa ada agenda/tugas yang mendekati batas waktu ya! ⏰",
            color=color,
            timestamp=dt_wib,
        )
        embed.add_field(
            name="📅 Batas Waktu",
            value=f"**{formatted_date}**\nPukul **{formatted_time} WIB**",
            inline=True,
        )
        embed.add_field(
            name="⏳ Sisa Waktu",
            value=f"**{time_label}**",
            inline=True,
        )
        if location:
            embed.add_field(
                name="📌 Info / Link Pengumpulan",
                value=location,
                inline=False,
            )
        embed.set_footer(text="KSM AIoT Deadline Reminder")
    else:
        title = f"📢 Pengingat: {event_name}"
        color = 0x5865F2  # Discord Blurple
        embed = discord.Embed(
            title=title,
            description=description
            or "Yuk siap-siap, sesi kegiatan kita sebentar lagi akan dimulai! ✨",
            color=color,
            timestamp=dt_wib,
        )
        embed.add_field(
            name="🗓️ Waktu Acara",
            value=f"**{formatted_date}**\nPukul **{formatted_time} WIB**",
            inline=True,
        )
        embed.add_field(
            name="⏰ Mulai Dalam",
            value=f"**{time_label}**",
            inline=True,
        )
        if location:
            embed.add_field(
                name="📍 Lokasi / Room",
                value=location,
                inline=False,
            )
        embed.set_footer(text="KSM AIoT Community Event • Waktu Indonesia Barat")

    if event_url:
        embed.url = event_url

    return embed


async def generate_dynamic_event_message(
    event_type: str,
    event_name: str,
    event_description: Optional[str] = None,
    fallback_text: str = "",
    role_mention: Optional[str] = None,
    timeout_sec: float = 120.0,
) -> str:
    """
    Generates a dynamic, contextual, friendly event message via LLM one-shot completion.
    Falls back gracefully to fallback_text (Jinja template) if LLM times out, fails, or is unavailable.
    """
    if event_type == "completed":
        system_instruction = (
            "You are Nexo, the friendly, casual, and supportive bot for KSM AIoT "
            "(Kelompok Studi Mahasiswa Artificial Intelligence of Things). "
            "Write a warm, concise Indonesian closing and thank-you announcement for a completed community event. "
            "Tone must be relaxed, natural, and encouraging. Use emojis naturally. "
            "Do NOT include markdown tables, headers, or quotes. Keep it to 1-2 short paragraphs."
        )
        user_prompt = (
            f"Event '{event_name}' baru saja resmi selesai.\n"
            f"Deskripsi/Topik Event: {event_description or 'Sesi diskusi dan kolaborasi seputar teknologi/AIoT'}.\n"
            "Buatkan pesan penutupan acara yang mengapresiasi kehadiran seluruh teman-teman KSM AIoT dan ajak mereka untuk menantikan event berikutnya!"
        )
    elif event_type == "started":
        system_instruction = (
            "You are Nexo, the friendly bot for KSM AIoT. "
            "Write an energetic, casual Indonesian announcement that an event has just started now. "
            "Keep it short, direct, and welcoming with natural emojis."
        )
        user_prompt = (
            f"Event '{event_name}' sekarang resmi dimulai!\n"
            f"Topik: {event_description or 'Sesi KSM AIoT'}.\n"
            "Ajak seluruh member untuk segera bergabung sekarang."
        )
    else:
        return fallback_text

    try:
        from utils.mcp_client import ai_client

        async def _call_llm():
            response = await ai_client.chat.completions.create(
                model=os.environ.get("LLM_MODEL_NAME", "gemma-4-e2b"),
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.7,
            )
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return ""

        generated_text = await asyncio.wait_for(_call_llm(), timeout=timeout_sec)
        if generated_text:
            if role_mention:
                generated_text = f"{generated_text}\n\n{role_mention}"
            return generated_text

    except Exception as e:
        logger.warning(
            f"Dynamic event message generation failed or timed out ({e}). Using static fallback template."
        )

    return fallback_text
