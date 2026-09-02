from datetime import datetime, timedelta
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
import re


def get_clean_schema(model: type[BaseModel]) -> dict[str, Any]:
    """
    Returns a token-efficient JSON schema representation of a Pydantic model
    using the centralized sanitize_parameters cleaner.
    """
    from utils.mcp_client import sanitize_parameters

    return sanitize_parameters(model.model_json_schema())


class DiscordEventSchema(BaseModel):
    name: str = Field(..., description="Event name (max 100 chars)")
    description: str = Field(
        ...,
        description="Topic/agenda of the event ONLY. Filter out any chat instructions meant for the bot",
    )
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time 24h (HH:MM:SS)")
    end_date: Optional[str] = Field(
        default=None,
        description="End date (YYYY-MM-DD). Optional.",
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End time 24h (HH:MM:SS). Optional.",
    )
    location: str = Field(..., description="Voice channel name, link, or location")
    target_role: Optional[str] = Field(
        default=None,
        description="Target mention if requested (e.g. '@everyone', role name). Optional.",
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def clean_time_string(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        match = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", str(v))
        if match:
            t = match.group(1)
            return t if len(t.split(":")) == 3 else f"{t}:00"
        return v

    @model_validator(mode="after")
    def populate_default_end_time(self) -> "DiscordEventSchema":
        """Otomatis isi end_date & end_time (+2 jam) jika tidak disertakan di prompt."""
        if not self.end_time or not self.end_date:
            try:
                start_dt = datetime.fromisoformat(
                    f"{self.start_date}T{self.start_time}"
                )
                end_dt = start_dt + timedelta(hours=2)
                if not self.end_date:
                    self.end_date = end_dt.strftime("%Y-%m-%d")
                if not self.end_time:
                    self.end_time = end_dt.strftime("%H:%M:%S")
            except Exception:
                pass
        return self


class ListDiscordEventsSchema(BaseModel):
    status_filter: Optional[str] = Field(
        default="all",
        description="Filter events: 'active', 'scheduled', or 'all'",
    )


class EndDiscordEventSchema(BaseModel):
    event_name: Optional[str] = Field(
        default=None,
        description="Event name or keyword to search and end (e.g. 'Diskusi Mingguan')",
    )
    event_id: Optional[int] = Field(
        default=None,
        description="Specific Discord Scheduled Event snowflake ID to end",
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
