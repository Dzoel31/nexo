from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CompetitionCreate(BaseModel):
    """Skema input untuk mendaftarkan info kompetisi / hackathon baru."""

    guild_id: int
    name: str
    category: str = "General"
    deadline: datetime
    channel_id: int
    created_by: int
    registration_url: str | None = None
    guidebook_url: str | None = None
    description: str | None = None
    target_role_id: int | None = None


class CompetitionRead(BaseModel):
    """Skema representasi data kompetisi / hackathon dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    guild_id: int
    name: str
    category: str
    deadline: datetime
    channel_id: int
    created_by: int
    registration_url: str | None = None
    guidebook_url: str | None = None
    description: str | None = None
    target_role_id: int | None = None
    reminders_sent: list[int] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
