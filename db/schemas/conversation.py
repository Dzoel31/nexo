from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from db.models import MessageRole


class MessageCreate(BaseModel):
    """Skema input untuk menyimpan pesan baru ke database."""

    role: MessageRole = Field(
        description="Role pengirim pesan (user, assistant, system, tool)"
    )
    content: str = Field(
        min_length=1,
        max_length=100_000,
        description="Isi teks konten percakapan",
    )
    token_count: int = Field(
        default=0,
        description="Jumlah token yang dihitung saat pesan dibuat",
    )


class MessageRead(BaseModel):
    """Skema representasi data pesan dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    token_count: int = 0
    created_at: datetime


class ConversationRead(BaseModel):
    """Skema representasi sesi percakapan pengguna."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    channel_id: int | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = Field(default_factory=list)
