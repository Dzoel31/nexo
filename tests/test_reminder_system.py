from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord
from utils.event_manager import (
    build_reminder_embed,
    detect_event_type,
    get_human_time_label,
    get_reminder_intervals_for_type,
    prune_reminder_intervals,
)
from cogs.server_events import ServerEvents


def test_detect_event_type():
    assert detect_event_type("[DL] Pengumpulan Laporan") == "DEADLINE"
    assert detect_event_type("[DEADLINE] KAK Proyek") == "DEADLINE"
    assert detect_event_type("Deadline Submit Proposal Lomba") == "DEADLINE"
    assert detect_event_type("Batas Akhir Revisi Anggaran") == "DEADLINE"
    assert detect_event_type("Tenggat Waktu LPJ") == "DEADLINE"
    assert detect_event_type("Agenda Bebas", is_all_day=True) == "DEADLINE"

    assert detect_event_type("Rapat Koordinasi Pengurus") == "EVENT"
    assert detect_event_type("Workshop IoT ESP32 & FreeRTOS") == "EVENT"
    assert detect_event_type("Sharing Session AIoT #3") == "EVENT"


def test_interval_profiles():
    deadline_intervals = get_reminder_intervals_for_type("DEADLINE")
    assert deadline_intervals == [10080, 4320, 1440, 720, 60]
    assert 30 not in deadline_intervals
    assert 10 not in deadline_intervals

    event_intervals = get_reminder_intervals_for_type("EVENT")
    assert event_intervals == [1440, 60]
    assert 10080 not in event_intervals
    assert 30 not in event_intervals


def test_human_time_labels():
    assert get_human_time_label(10080) == "H-7 Hari"
    assert get_human_time_label(4320) == "H-3 Hari"
    assert get_human_time_label(1440) == "H-1 Hari"
    assert get_human_time_label(720) == "12 Jam Lagi"
    assert get_human_time_label(60) == "1 Jam Lagi"


def test_prune_reminder_intervals_by_type():
    now = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)

    # Event starts in 2 days (2880 mins from now)
    start_in_2d = now + timedelta(days=2)

    # For DEADLINE (profiles: 10080, 4320, 1440, 720, 60):
    # 10080 (7d) & 4320 (3d) are already in the past, so only 1440, 720, 60 valid
    deadline_pruned = prune_reminder_intervals(
        start_in_2d, now_dt=now, event_type="DEADLINE"
    )
    assert deadline_pruned == [1440, 720, 60]

    # For EVENT (profiles: 1440, 60):
    event_pruned = prune_reminder_intervals(start_in_2d, now_dt=now, event_type="EVENT")
    assert event_pruned == [1440, 60]


def test_build_reminder_embed():
    start_dt = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)

    # DEADLINE Embed
    dl_embed = build_reminder_embed(
        event_name="[DL] Submit Proposal",
        description="Harap kumpulkan sebelum batas waktu",
        start_dt=start_dt,
        location="Google Classroom",
        interval_minutes=1440,
        event_type="DEADLINE",
    )
    assert dl_embed.color.value == 0xEF4444
    assert "Deadline" in dl_embed.title
    assert any("Batas Waktu" in f.name for f in dl_embed.fields)

    # EVENT Embed
    ev_embed = build_reminder_embed(
        event_name="Workshop ESP32",
        description="Sesi lab langsung",
        start_dt=start_dt,
        location="Lab IoT",
        interval_minutes=60,
        event_type="EVENT",
    )
    assert ev_embed.color.value == 0x5865F2
    assert "Pengingat" in ev_embed.title
    assert any("Waktu Acara" in f.name for f in ev_embed.fields)


@pytest.mark.asyncio
async def test_reminder_loop_deduplication_and_embed_send():
    bot = MagicMock()
    bot.wait_until_ready = AsyncMock()
    channel = AsyncMock()
    bot.get_channel = MagicMock(return_value=channel)
    bot.guilds = [MagicMock()]

    now_utc = datetime.now(timezone.utc)
    ev_start = now_utc + timedelta(
        minutes=45
    )  # 45 mins from now -> 60m reminder is due!
    ev_end = ev_start + timedelta(hours=2)

    ev_mock = MagicMock()
    ev_mock.id = 123456
    ev_mock.name = "Rapat Divisi"
    ev_mock.description = "Bahas Proyek"
    ev_mock.location = "Voice Room"
    ev_mock.event_url = "https://discord.com/events/123/123456"
    ev_mock.start_time = ev_start
    ev_mock.end_time = ev_end
    ev_mock.broadcast_channel_id = 999
    ev_mock.target_role_id = None
    ev_mock.is_active = True
    ev_mock.reminder_intervals = [1440, 60]
    ev_mock.reminders_sent = [1440]  # 1440 already sent, 60 is pending

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()
    cog.sync_events_from_gcal.cancel()

    with patch("cogs.server_events.async_session") as mock_session_ctx:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(all=MagicMock(return_value=[ev_mock]))
                )
            )
        )
        mock_session_ctx.return_value.__aenter__.return_value = mock_session

        # Run one iteration logic of reminder_loop
        await cog.reminder_loop()

        # Check channel.send was called with embed
        assert channel.send.called
        kwargs = channel.send.call_args.kwargs
        assert "embed" in kwargs
        assert isinstance(kwargs["embed"], discord.Embed)

        # Ensure cache recorded (123456, 60)
        assert (123456, 60) in cog._reminded_cache
        assert 60 in ev_mock.reminders_sent
