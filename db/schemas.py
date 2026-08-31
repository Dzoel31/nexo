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


class MessageRead(BaseModel):
    """Skema representasi data pesan dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
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


class LLMMessagePayload(BaseModel):
    """Format standar payload pesan yang dikirimkan ke model LLM."""

    role: str = Field(
        description="Role pesan dalam format string yang dikenali LLM API"
    )
    content: str = Field(description="Isi pesan prompt/jawaban")


class ConversationContext(BaseModel):
    """Ringkasan masa lalu dan kumpulan pesan aktif untuk diumpankan ke LLM."""

    summary: str | None = Field(
        default=None, description="Rolling summary dari percakapan sebelumnya"
    )
    messages: list[LLMMessagePayload] = Field(
        default_factory=list,
        description="Daftar pesan aktif terkini yang muat dalam anggaran token",
    )
