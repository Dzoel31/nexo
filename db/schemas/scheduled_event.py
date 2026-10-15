from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
