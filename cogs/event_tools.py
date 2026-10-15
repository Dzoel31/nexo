from collections.abc import Callable
from typing import Any

from utils.schemas import (
    CheckVoiceChannelSchema,
    ClearMessagesSchema,
    DiscordEventSchema,
    DiscordPollSchema,
    DiscordThreadSchema,
    EndDiscordEventSchema,
    EndDiscordPollSchema,
    GetServerChannelsSchema,
    GetServerRolesSchema,
    ListDiscordEventsSchema,
    get_clean_schema,
)

TOOL_NAMES = {
    "list_discord_events",
    "create_discord_event",
    "end_discord_event",
    "create_discord_thread",
    "create_discord_poll",
    "end_discord_poll",
    "get_server_channels",
    "get_server_roles",
    "clear_messages",
    "check_voice_channel",
}


def register_event_tools(
    bot: Any,
    handlers: dict[str, Callable[..., Any]],
) -> None:
    """Register scheduled-event and server tools on the shared bot registry."""
    if not hasattr(bot, "ai_tools"):
        bot.ai_tools = []
    if not hasattr(bot, "local_tool_handlers"):
        bot.local_tool_handlers = {}

    bot.ai_tools = [
        tool
        for tool in bot.ai_tools
        if tool.get("function", {}).get("name") not in TOOL_NAMES
    ]

    tool_specs = (
        (
            "list_discord_events",
            "List scheduled and active events on the server.",
            ListDiscordEventsSchema,
        ),
        (
            "create_discord_event",
            "Schedule a new server event or meeting.",
            DiscordEventSchema,
        ),
        (
            "end_discord_event",
            "End, close, or stop a Discord Scheduled Event.",
            EndDiscordEventSchema,
        ),
        (
            "create_discord_thread",
            "Create a new thread in the current channel.",
            DiscordThreadSchema,
        ),
        (
            "create_discord_poll",
            "Create an interactive native poll.",
            DiscordPollSchema,
        ),
        (
            "end_discord_poll",
            "End an active poll and get final votes.",
            EndDiscordPollSchema,
        ),
        (
            "get_server_channels",
            "List all server text and voice channels.",
            GetServerChannelsSchema,
        ),
        (
            "get_server_roles",
            "List all server roles and IDs.",
            GetServerRolesSchema,
        ),
        (
            "clear_messages",
            "Delete messages in bulk.",
            ClearMessagesSchema,
        ),
        (
            "check_voice_channel",
            "List users in a voice channel.",
            CheckVoiceChannelSchema,
        ),
    )

    for name, description, schema in tool_specs:
        bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": get_clean_schema(schema),
                },
            }
        )
        bot.local_tool_handlers[name] = handlers[name]
