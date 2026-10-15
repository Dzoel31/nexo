import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from db.schemas.scheduled_announcement import (
    ScheduledAnnouncementCreate,
    ScheduledAnnouncementRead,
)
from db.session import async_session


async def create_scheduled_announcement(
    guild_id: int,
    channel_id: int,
    author_id: int,
    content: str,
    scheduled_at: datetime,
    is_embed: bool = False,
    title: str | None = None,
) -> ScheduledAnnouncementRead:
    """Validates and creates a scheduled announcement using raw SQL."""
    payload = ScheduledAnnouncementCreate(
        guild_id=guild_id,
        channel_id=channel_id,
        author_id=author_id,
        content=content,
        scheduled_at=scheduled_at,
        is_embed=is_embed,
        title=title,
    )
    new_id = uuid.uuid4()
    now_utc = datetime.now(UTC)
    async with async_session() as session:
        insert_sql = text("""
            INSERT INTO scheduled_announcements (
                id, guild_id, channel_id, author_id, content, is_embed, title, scheduled_at, status, created_at
            )
            VALUES (
                :id, :guild_id, :channel_id, :author_id, :content, :is_embed, :title, :scheduled_at, 'pending', :now_utc
            )
            RETURNING id, guild_id, channel_id, author_id, content, is_embed, title, scheduled_at, status, created_at
        """)
        res = await session.execute(
            insert_sql,
            {
                "id": new_id,
                "guild_id": payload.guild_id,
                "channel_id": payload.channel_id,
                "author_id": payload.author_id,
                "content": payload.content,
                "is_embed": payload.is_embed,
                "title": payload.title,
                "scheduled_at": payload.scheduled_at,
                "now_utc": now_utc,
            },
        )
        await session.commit()
        row = res.mappings().first()
        return ScheduledAnnouncementRead.model_validate(dict(row))


async def get_due_scheduled_announcements(
    now_utc: datetime,
) -> list[ScheduledAnnouncementRead]:
    """Retrieves all pending announcements scheduled on or before now_utc using raw SQL."""
    async with async_session() as session:
        select_sql = text("""
            SELECT id, guild_id, channel_id, author_id, content, is_embed, title, scheduled_at, status, created_at
            FROM scheduled_announcements
            WHERE status = 'pending' AND scheduled_at <= :now_utc
            ORDER BY scheduled_at ASC
        """)
        result = await session.execute(select_sql, {"now_utc": now_utc})
        rows = result.mappings().all()
        return [ScheduledAnnouncementRead.model_validate(dict(r)) for r in rows]


async def mark_announcement_status(announcement_id: UUID, status: str) -> None:
    """Updates the status of a scheduled announcement using raw SQL."""
    async with async_session() as session:
        update_sql = text("""
            UPDATE scheduled_announcements
            SET status = :status
            WHERE id = :announcement_id
        """)
        await session.execute(
            update_sql, {"status": status, "announcement_id": announcement_id}
        )
        await session.commit()


async def list_pending_announcements(guild_id: int) -> list[ScheduledAnnouncementRead]:
    """Lists all pending announcements for a guild ordered by scheduled_at using raw SQL."""
    async with async_session() as session:
        select_sql = text("""
            SELECT id, guild_id, channel_id, author_id, content, is_embed, title, scheduled_at, status, created_at
            FROM scheduled_announcements
            WHERE guild_id = :guild_id AND status = 'pending'
            ORDER BY scheduled_at ASC
        """)
        result = await session.execute(select_sql, {"guild_id": guild_id})
        rows = result.mappings().all()
        return [ScheduledAnnouncementRead.model_validate(dict(r)) for r in rows]


async def cancel_scheduled_announcement(announcement_id: UUID, guild_id: int) -> bool:
    """Cancels a pending announcement using raw SQL."""
    async with async_session() as session:
        update_sql = text("""
            UPDATE scheduled_announcements
            SET status = 'cancelled'
            WHERE id = :announcement_id AND guild_id = :guild_id AND status = 'pending'
        """)
        res = await session.execute(
            update_sql, {"announcement_id": announcement_id, "guild_id": guild_id}
        )
        await session.commit()
        return res.rowcount > 0
