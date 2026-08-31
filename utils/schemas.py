from typing import List, Optional
from pydantic import BaseModel, Field


class DiscordEventSchema(BaseModel):
    name: str = Field(..., description="Event name (max 100 chars)")
    description: str = Field(..., description="Event description")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time (HH:MM:SS WIB)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    end_time: Optional[str] = Field(default=None, description="End time (HH:MM:SS WIB)")
    location: str = Field(..., description="Voice channel name, link, or location")


class EndDiscordEventSchema(BaseModel):
    event_id: Optional[int] = Field(
        default=None,
        description="Scheduled Event ID to end (omit to auto-find active/latest event)",
    )


class DiscordThreadSchema(BaseModel):
    name: str = Field(..., description="Thread name (max 100 chars)")
    reason: str = Field(..., description="Reason for creating thread")


class DiscordPollSchema(BaseModel):
    question: str = Field(..., description="Poll question")
    options: List[str] = Field(..., description="Poll choices (max 10 items)")
    allow_multiselect: bool = Field(default=False, description="Allow multiple choices")
    duration_hours: int = Field(default=24, description="Duration in hours (1-168)")


class EndDiscordPollSchema(BaseModel):
    message_id: Optional[int] = Field(
        default=None,
        description="Target poll message ID (omit to auto-find in current channel)",
    )


class GetServerChannelsSchema(BaseModel):
    pass


class GetServerRolesSchema(BaseModel):
    pass


class ClearMessagesSchema(BaseModel):
    limit: int = Field(
        default=100, description="Number of messages to scan/delete (max 500)"
    )
    only_today: bool = Field(
        default=False, description="Only delete messages sent today"
    )


class CheckVoiceChannelSchema(BaseModel):
    channel_name: Optional[str] = Field(
        default=None,
        description="Voice channel name (omit for current/active user channel)",
    )
