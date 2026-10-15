from __future__ import annotations

import re
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator, model_validator


class DiscordEventSchema(BaseModel):
    name: str = Field(..., description="Event name (max 100 chars)")
    description: str = Field(
        ...,
        description="Topic/agenda of the event ONLY. Filter out any chat instructions meant for the bot",
    )
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time 24h (HH:MM:SS)")
    end_date: str | None = Field(
        default=None,
        description="End date (YYYY-MM-DD). Optional.",
    )
    end_time: str | None = Field(
        default=None,
        description="End time 24h (HH:MM:SS). Optional.",
    )
    location: str = Field(..., description="Voice channel name, link, or location")
    target_role: str | None = Field(
        default=None,
        description="Target mention if requested (e.g. '@everyone', role name). Optional.",
    )

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def clean_time_string(cls, v: str | None) -> str | None:
        if not v:
            return v
        match = re.search(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b", str(v))
        if match:
            t = match.group(1)
            return t if len(t.split(":")) == 3 else f"{t}:00"
        return v

    @model_validator(mode="after")
    def populate_default_end_time(self) -> DiscordEventSchema:
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
            except Exception:  # noqa: S110, BLE001
                pass
        return self


class ListDiscordEventsSchema(BaseModel):
    status_filter: str | None = Field(
        default="all",
        description="Filter events: 'active', 'scheduled', or 'all'",
    )


class EndDiscordEventSchema(BaseModel):
    event_name: str | None = Field(
        default=None,
        description="Event name or keyword to search and end (e.g. 'Diskusi Mingguan')",
    )
    event_id: int | None = Field(
        default=None,
        description="Specific Discord Scheduled Event snowflake ID to end",
    )
