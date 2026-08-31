from pydantic import BaseModel, Field
from typing import Optional, List


class DiscordEventSchema(BaseModel):
    name: str = Field(..., description="Event name, max 100 characters")
    description: str = Field(..., description="Full description of the event")
    start_date: str = Field(
        ..., description="Event start date format YYYY-MM-DD (e.g.: 2026-07-01)"
    )
    start_time: str = Field(
        ...,
        description="Event start time format HH:MM:SS (e.g.: 22:00:00). 24-hour format.",
    )
    end_date: Optional[str] = Field(
        default=None, description="Event end date format YYYY-MM-DD (optional)"
    )
    end_time: Optional[str] = Field(
        default=None, description="Event end time format HH:MM:SS (optional)"
    )
    location: str = Field(
        ...,
        description="Event location. If in a Voice/Stage Channel, write the channel name exactly (e.g., 'General'). If outside the server, write the place name or link.",
    )


class DiscordThreadSchema(BaseModel):
    name: str = Field(..., description="Thread name, max 100 characters")
    reason: str = Field(
        ...,
        description="Brief reason why this thread was created (appears in audit log)",
    )


class DiscordPollSchema(BaseModel):
    question: str = Field(..., description="Poll question")
    options: List[str] = Field(
        ..., description="List of poll options (maximum 10 options)"
    )
    allow_multiselect: bool = Field(
        default=False, description="Whether the user can select more than one option"
    )
    duration_hours: int = Field(
        default=24, description="Poll duration in hours (maximum 168 hours)"
    )


class EndDiscordPollSchema(BaseModel):
    message_id: Optional[int] = Field(
        default=None,
        description="The ID of the message containing the poll to end. If not provided, the bot will automatically search for the latest active poll in the current channel.",
    )


class GetServerChannelsSchema(BaseModel):
    pass


class GetServerRolesSchema(BaseModel):
    pass


class ClearMessagesSchema(BaseModel):
    limit: int = Field(
        default=100,
        description="Number of message history to be checked/deleted (maximum 500)",
    )
    only_today: bool = Field(
        default=False, description="If true, only delete messages sent today"
    )


class CheckVoiceChannelSchema(BaseModel):
    channel_name: Optional[str] = Field(
        default=None,
        description="Name of the Voice Channel to check (case-insensitive, e.g., 'Meeting'). Optional: if omitted, defaults to the current channel or the user's active voice channel.",
    )
