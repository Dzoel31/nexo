"""Legacy compatibility facade. Do not add new logic here."""

from schemas.discord import (
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
)
from utils.schema_utils import get_clean_schema

__all__ = [
    "CheckVoiceChannelSchema",
    "ClearMessagesSchema",
    "DiscordEventSchema",
    "DiscordPollSchema",
    "DiscordThreadSchema",
    "EndDiscordEventSchema",
    "EndDiscordPollSchema",
    "FindServerMembersSchema",
    "GetServerChannelsSchema",
    "GetServerRolesSchema",
    "ListDiscordEventsSchema",
    "NotifyMemberSchema",
    "get_clean_schema",
]
