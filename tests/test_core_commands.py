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
