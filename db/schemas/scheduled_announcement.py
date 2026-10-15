from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduledAnnouncementCreate(BaseModel):
    """Skema input untuk membuat pengumuman terjadwal."""

    guild_id: int
    channel_id: int
    author_id: int
    content: str
    scheduled_at: datetime
    is_embed: bool = False
    title: str | None = None


class ScheduledAnnouncementRead(BaseModel):
    """Skema representasi data pengumuman terjadwal dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    guild_id: int
    channel_id: int
    author_id: int
    content: str
    is_embed: bool = False
    title: str | None = None
    scheduled_at: datetime
    status: str = "pending"
    created_at: datetime
