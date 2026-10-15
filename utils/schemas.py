"""Legacy compatibility facade. Do not add new logic here."""

from schemas.discord import (
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
    "GetServerChannelsSchema",
    "GetServerRolesSchema",
    "ListDiscordEventsSchema",
    "get_clean_schema",
]
