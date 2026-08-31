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


class ScheduledEventCreate(BaseModel):
    """Skema input untuk persistensi Discord Event baru ke database."""

    id: int = Field(description="ID native Discord Scheduled Event")
    guild_id: int = Field(description="ID Guild Discord")
    broadcast_channel_id: int = Field(description="ID Kanal Broadcast Pengumuman")
    broadcast_message_id: int | None = Field(
        default=None, description="ID Pesan Broadcast Awal"
    )
    name: str = Field(description="Nama Acara")
    description: str | None = Field(default=None, description="Deskripsi Acara")
    location: str = Field(description="Lokasi Acara")
    start_time: datetime = Field(description="Waktu Mulai Acara (Timezone Aware)")
    end_time: datetime | None = Field(
        default=None, description="Waktu Selesai Acara (Timezone Aware)"
    )
    event_url: str = Field(description="URL link Discord Scheduled Event")
    reminder_intervals: list[int] = Field(
        default_factory=list,
        description="Daftar interval pengingat dalam menit yang tersaring",
    )
    reminders_sent: list[int] = Field(
        default_factory=list,
        description="Daftar interval pengingat dalam menit yang sudah terkirim",
    )
    template_name: str = Field(
        default="default_reminder.j2", description="Nama file template Jinja2"
    )
    target_role_id: int | None = Field(
        default=None, description="ID role target mention"
    )
    is_active: bool = Field(default=True, description="Status keaktifan event")


class ScheduledEventRead(BaseModel):
    """Skema representasi data Discord Scheduled Event dari database."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    guild_id: int
    broadcast_channel_id: int
    broadcast_message_id: int | None
    name: str
    description: str | None
    location: str
    start_time: datetime
    end_time: datetime | None
    event_url: str
    reminder_intervals: list[int]
    reminders_sent: list[int]
    template_name: str
    target_role_id: int | None
    is_active: bool
    created_at: datetime
