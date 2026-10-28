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
    FindServerMembersSchema,
    GetServerChannelsSchema,
    GetServerRolesSchema,
    ListDiscordEventsSchema,
    NotifyMemberSchema,
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
    "find_server_members",
    "notify_member",
}

READ_ONLY_TOOL_NAMES = {
    "list_discord_events",
    "get_server_channels",
    "get_server_roles",
    "check_voice_channel",
    "find_server_members",
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
        (
            "find_server_members",
            "Find server members by name. This search never sends a mention or message.",
            FindServerMembersSchema,
        ),
        (
            "notify_member",
            "Send a message to one exact member selected by Discord ID. Use only when the user explicitly asks to notify or tag someone; never use for a search-only question.",
            NotifyMemberSchema,
        ),
    )

    for name, description, schema in tool_specs:
        bot.ai_tools.append(
            {
                "type": "function",
                "readOnlyHint": name in READ_ONLY_TOOL_NAMES,
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": get_clean_schema(schema),
                },
            }
        )
        bot.local_tool_handlers[name] = handlers[name]
