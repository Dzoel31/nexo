from unittest.mock import AsyncMock, MagicMock
import pytest
from cogs.core_commands import CoreCommands


class MockPermissions:
    def __init__(self, manage_messages=True):
        self.manage_messages = manage_messages
        self.administrator = False


def create_ctx(manage_messages=True, is_owner=False):
    ctx = MagicMock()
    member = MagicMock()
    member.id = 111111111
    member.guild_permissions = MockPermissions(manage_messages=manage_messages)
    member.guild = MagicMock()
    member.guild.owner_id = 111111111 if is_owner else 999999999
    member.roles = []
    ctx.author = member
    ctx.guild = member.guild
    ctx.send = AsyncMock()
    ctx.message = MagicMock()
    ctx.message.delete = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_say_command_unauthorized():
    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=False)

    await cog.say.callback(cog, ctx, text="to #general Halo guys")
    ctx.send.assert_awaited_once()
    args, kwargs = ctx.send.call_args
    assert "Akses Ditolak" in args[0]


@pytest.mark.asyncio
async def test_say_command_success():
    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=True)

    target_channel = MagicMock()
    target_channel.name = "general"
    target_channel.send = AsyncMock()
    ctx.guild.get_channel.return_value = target_channel

    await cog.say.callback(cog, ctx, text="to <#123456> Selamat malam semua!")
    target_channel.send.assert_awaited_once()
    msg_sent, _ = target_channel.send.call_args
    assert msg_sent[0] == "Selamat malam semua!"
    ctx.message.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_say_command_smart_mentions():
    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=True)

    target_channel = MagicMock()
    target_channel.name = "announcements"
    target_channel.send = AsyncMock()
    ctx.guild.get_channel.return_value = target_channel
    ctx.guild.text_channels = [target_channel]

    # Setup roles
    role = MagicMock()
    role.id = 888888
    role.name = "Staff-Core"
    role.is_default.return_value = False
    role.mention = "<@&888888>"
    ctx.guild.roles = [role]
    ctx.guild.get_role.side_effect = lambda rid: role if rid == 888888 else None

    # Setup members
    member = MagicMock()
    member.id = 777777777777777777
    member.name = "budi_santoso"
    member.display_name = "Budi Santoso"
    member.global_name = "Budi"
    member.mention = "<@777777777777777777>"
    ctx.guild.members = [member]

    # Test mentions: role (@Staff-Core), raw ID (@777777777777777777), member name (@"Budi Santoso"), and broadcast (@everyone)
    input_text = 'to #announcements Halo @everyone! Tolong @Staff-Core, @"Budi Santoso", dan @777777777777777777 segera kumpul.'
    await cog.say.callback(cog, ctx, text=input_text)

    target_channel.send.assert_awaited_once()
    msg_sent, kwargs = target_channel.send.call_args
    sent_text = msg_sent[0]

    assert "@everyone" in sent_text
    assert "<@&888888>" in sent_text
    assert "<@777777777777777777>" in sent_text
    assert kwargs["allowed_mentions"].everyone is True


@pytest.mark.asyncio
async def test_say_command_embed_mode():
    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=True)
    ctx.guild.name = "KSM AIoT Server"
    ctx.guild.icon = None

    target_channel = MagicMock()
    target_channel.name = "pengumuman"
    target_channel.send = AsyncMock()
    ctx.guild.get_channel.return_value = target_channel
    ctx.guild.text_channels = [target_channel]
    ctx.guild.roles = []
    ctx.guild.members = []

    # Test embed mode with title and broadcast ping
    input_text = 'to #pengumuman --embed --title "Rapat Divisi" @everyone Rapat dimulai pukul 19:00 WIB!'
    await cog.say.callback(cog, ctx, text=input_text)

    target_channel.send.assert_awaited_once()
    _, kwargs = target_channel.send.call_args
    assert kwargs["embed"] is not None
    assert kwargs["embed"].title == "Rapat Divisi"
    assert "Rapat dimulai pukul 19:00 WIB!" in kwargs["embed"].description
    # Ensure ping is forwarded in content so Discord delivers notification
    assert kwargs["content"] == "@everyone"


def test_parse_scheduled_time_flags():
    from datetime import datetime, timezone
    from cogs.core_commands import parse_scheduled_time

    # Test --time flag
    sched_dt, cleaned = parse_scheduled_time('Halo semua --time "2026-10-15 14:30"')
    assert sched_dt is not None
    assert sched_dt.year == 2026
    assert sched_dt.month == 10
    assert sched_dt.day == 15
    # 14:30 WIB is 07:30 UTC
    assert sched_dt.hour == 7
    assert sched_dt.minute == 30
    assert cleaned == "Halo semua"

    # Test --in flag (e.g. 30m, 2h, 1d)
    now_utc = datetime.now(timezone.utc)
    sched_dt_in, cleaned_in = parse_scheduled_time("Pengingat rapat --in 2h")
    assert sched_dt_in is not None
    diff = (sched_dt_in - now_utc).total_seconds()
    # Approx 7200 seconds (+- 5 seconds)
    assert 7190 <= diff <= 7210
    assert cleaned_in == "Pengingat rapat"


@pytest.mark.asyncio
async def test_say_command_schedule_in(monkeypatch):
    import uuid
    from unittest.mock import AsyncMock, patch

    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=True)

    target_channel = MagicMock()
    target_channel.id = 123456
    target_channel.name = "pengumuman"
    target_channel.mention = "<#123456>"
    ctx.guild.get_channel.return_value = target_channel
    ctx.guild.text_channels = [target_channel]

    mock_announcement = MagicMock()
    mock_announcement.id = uuid.uuid4()

    with patch(
        "cogs.core_commands.create_scheduled_announcement",
        new=AsyncMock(return_value=mock_announcement),
    ) as mock_create:
        input_text = "to #pengumuman --in 1h Pengumuman rapat penting!"
        await cog.say.callback(cog, ctx, text=input_text)

        mock_create.assert_awaited_once()
        ctx.send.assert_awaited_once()
        sent_msg = ctx.send.call_args[0][0]
        assert "Pengumuman Berhasil Dijadwalkan" in sent_msg
        assert str(mock_announcement.id) in sent_msg


@pytest.mark.asyncio
async def test_say_command_list_and_cancel(monkeypatch):
    import uuid
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock, patch

    bot = MagicMock()
    cog = CoreCommands(bot)
    ctx = create_ctx(manage_messages=True)

    mock_item = MagicMock()
    test_id = uuid.uuid4()
    mock_item.id = test_id
    mock_item.channel_id = 123456
    mock_item.content = "Pengumuman terjadwal nomor satu"
    mock_item.scheduled_at = datetime.now(timezone.utc)
    mock_item.is_embed = False

    target_channel = MagicMock()
    target_channel.mention = "<#123456>"
    ctx.guild.get_channel.return_value = target_channel

    # Test $say list with items
    with patch(
        "cogs.core_commands.list_pending_announcements",
        new=AsyncMock(return_value=[mock_item]),
    ):
        await cog.say.callback(cog, ctx, text="list")
        ctx.send.assert_awaited_once()
        embed = ctx.send.call_args[1]["embed"]
        assert "Antrean Pengumuman Terjadwal" in embed.title

    # Test $say cancel valid id
    ctx.send.reset_mock()
    with patch(
        "cogs.core_commands.cancel_scheduled_announcement",
        new=AsyncMock(return_value=True),
    ):
        await cog.say.callback(cog, ctx, text=f"cancel {test_id}")
        ctx.send.assert_awaited_once()
        assert "berhasil dibatalkan" in ctx.send.call_args[0][0]
