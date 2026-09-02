import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import discord
from utils.schemas import (
    EndDiscordEventSchema,
    ListDiscordEventsSchema,
    get_clean_schema,
)
from cogs.server_events import ServerEvents


class MockPermissions:
    def __init__(self, **kwargs):
        self.administrator = kwargs.get("administrator", True)
        self.manage_events = kwargs.get("manage_events", True)
        self.manage_messages = kwargs.get("manage_messages", True)


def create_mock_admin_ctx(guild=None):
    ctx = MagicMock()
    member = MagicMock()
    member.id = 111111111
    member.guild_permissions = MockPermissions(
        administrator=True, manage_events=True, manage_messages=True
    )
    g = guild if guild is not None else MagicMock()
    g.owner_id = 111111111
    member.guild = g
    member.roles = []
    ctx.author = member
    ctx.guild = g
    ctx.channel = MagicMock()
    return ctx


def create_mock_unauthorized_ctx(guild=None):
    ctx = MagicMock()
    member = MagicMock()
    member.id = 222222222
    member.guild_permissions = MockPermissions(
        administrator=False, manage_events=False, manage_messages=False
    )
    g = guild if guild is not None else MagicMock()
    g.owner_id = 999999999
    member.guild = g
    member.roles = []
    ctx.author = member
    ctx.guild = g
    ctx.channel = MagicMock()
    return ctx


def test_get_clean_schema():
    schema = get_clean_schema(EndDiscordEventSchema)
    assert "title" not in schema
    assert "$defs" not in schema
    assert "properties" in schema
    assert "event_name" in schema["properties"]
    assert "title" not in schema["properties"]["event_name"]
    assert "event_id" in schema["properties"]
    assert "title" not in schema["properties"]["event_id"]


def test_list_discord_events_schema_validation():
    data = ListDiscordEventsSchema(status_filter="active")
    assert data.status_filter == "active"

    data_default = ListDiscordEventsSchema()
    assert data_default.status_filter == "all"


@pytest.mark.asyncio
async def test_list_events_handler_empty():
    bot = MagicMock()
    guild = MagicMock()
    guild.fetch_scheduled_events = AsyncMock(return_value=[])
    bot.guilds = [guild]

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    res = await cog.list_events_handler({"status_filter": "all"})
    assert res == "Tidak ada acara terjadwal di server saat ini."


@pytest.mark.asyncio
async def test_list_events_handler_formatted():
    bot = MagicMock()
    guild = MagicMock()

    ev1 = MagicMock()
    ev1.id = 111222333
    ev1.name = "Workshop IoT ESP32"
    ev1.status = discord.EventStatus.active
    ev1.start_time = datetime(2026, 9, 2, 12, 30, tzinfo=timezone.utc)

    ev2 = MagicMock()
    ev2.id = 444555666
    ev2.name = "Diskusi AI Agent"
    ev2.status = discord.EventStatus.scheduled
    ev2.start_time = datetime(2026, 9, 3, 14, 0, tzinfo=timezone.utc)

    guild.fetch_scheduled_events = AsyncMock(return_value=[ev1, ev2])
    bot.guilds = [guild]

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    res = await cog.list_events_handler({"status_filter": "all"})
    assert "[ACTIVE] Workshop IoT ESP32" in res
    assert "[SCHEDULED] Diskusi AI Agent" in res
    assert "111222333" in res


@pytest.mark.asyncio
async def test_end_event_handler_by_id():
    bot = MagicMock()
    guild = MagicMock()

    ev1 = MagicMock()
    ev1.id = 999888
    ev1.name = "Sesi Sharing Session"
    ev1.description = "Sharing seputar embedded system"
    ev1.location = "Voice Room 1"
    ev1.status = discord.EventStatus.active
    ev1.end = AsyncMock()
    ev1.delete = AsyncMock()

    guild.get_scheduled_event = MagicMock(return_value=ev1)
    guild.system_channel = None
    bot.guilds = [guild]
    bot.get_channel = MagicMock(return_value=None)

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    admin_ctx = create_mock_admin_ctx(guild=guild)

    with patch("cogs.server_events.async_session") as mock_session_ctx:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_session_ctx.return_value.__aenter__.return_value = mock_session

        res = await cog.end_event_handler({"event_id": 999888}, ctx_obj=admin_ctx)
        assert "✅ Acara 'Sesi Sharing Session' berhasil diakhiri" in res
        ev1.end.assert_awaited_once()


@pytest.mark.asyncio
async def test_end_event_handler_by_name_partial_match():
    bot = MagicMock()
    guild = MagicMock()

    ev1 = MagicMock()
    ev1.id = 12345
    ev1.name = "Weekly Discussion KSM AIoT #1"
    ev1.description = "Weekly topic"
    ev1.location = "Voice Channel"
    ev1.status = discord.EventStatus.scheduled
    ev1.cancel = AsyncMock()
    ev1.delete = AsyncMock()

    guild.get_scheduled_event = MagicMock(return_value=None)
    guild.fetch_scheduled_events = AsyncMock(return_value=[ev1])
    guild.system_channel = None
    bot.guilds = [guild]
    bot.get_channel = MagicMock(return_value=None)

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    admin_ctx = create_mock_admin_ctx(guild=guild)

    with patch("cogs.server_events.async_session") as mock_session_ctx:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        mock_session_ctx.return_value.__aenter__.return_value = mock_session

        res = await cog.end_event_handler(
            {"event_name": "weekly discussion"}, ctx_obj=admin_ctx
        )
        assert "✅ Acara 'Weekly Discussion KSM AIoT #1' berhasil diakhiri" in res
        ev1.cancel.assert_awaited_once()


@pytest.mark.asyncio
async def test_end_event_handler_unauthorized():
    bot = MagicMock()
    guild = MagicMock()
    bot.guilds = [guild]

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    unauth_ctx = create_mock_unauthorized_ctx(guild=guild)

    res = await cog.end_event_handler({"event_name": "Some Event"}, ctx_obj=unauth_ctx)
    assert (
        "❌ DITOLAK: Kamu tidak memiliki izin 'Manage Events' atau peran kepengurusan"
        in res
    )


@pytest.mark.asyncio
async def test_end_event_handler_not_found():
    bot = MagicMock()
    guild = MagicMock()
    guild.get_scheduled_event = MagicMock(return_value=None)
    guild.fetch_scheduled_events = AsyncMock(return_value=[])
    bot.guilds = [guild]

    cog = ServerEvents(bot)
    cog.reminder_loop.cancel()

    admin_ctx = create_mock_admin_ctx(guild=guild)

    res = await cog.end_event_handler(
        {"event_name": "Non Existing Event"}, ctx_obj=admin_ctx
    )
    assert (
        "❌ Tidak ditemukan acara dengan nama/keyword 'Non Existing Event' di server."
        in res
    )
