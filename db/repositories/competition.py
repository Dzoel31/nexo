from datetime import UTC, datetime

from sqlalchemy import JSON, bindparam, text

from db.schemas.competition import CompetitionCreate, CompetitionRead
from db.session import async_session


async def create_competition(
    guild_id: int,
    name: str,
    category: str,
    deadline: datetime,
    channel_id: int,
    created_by: int,
    registration_url: str | None = None,
    guidebook_url: str | None = None,
    description: str | None = None,
    target_role_id: int | None = None,
) -> CompetitionRead:
    """Validates and registers a new competition into radar using raw SQL."""
    payload = CompetitionCreate(
        guild_id=guild_id,
        name=name,
        category=category,
        deadline=deadline,
        channel_id=channel_id,
        created_by=created_by,
        registration_url=registration_url,
        guidebook_url=guidebook_url,
        description=description,
        target_role_id=target_role_id,
    )
    now_utc = datetime.now(UTC)
    async with async_session() as session:
        insert_sql = text("""
            INSERT INTO competitions (
                guild_id, name, category, deadline, channel_id, created_by,
                registration_url, guidebook_url, description, target_role_id,
                reminders_sent, is_active, created_at
            )
            VALUES (
                :guild_id, :name, :category, :deadline, :channel_id, :created_by,
                :registration_url, :guidebook_url, :description, :target_role_id,
                :reminders_sent, TRUE, :now_utc
            )
            RETURNING id, guild_id, name, category, deadline, channel_id, created_by,
                      registration_url, guidebook_url, description, target_role_id,
                      reminders_sent, is_active, created_at
        """).bindparams(bindparam("reminders_sent", type_=JSON))

        res = await session.execute(
            insert_sql,
            {
                "guild_id": payload.guild_id,
                "name": payload.name,
                "category": payload.category,
                "deadline": payload.deadline,
                "channel_id": payload.channel_id,
                "created_by": payload.created_by,
                "registration_url": payload.registration_url,
                "guidebook_url": payload.guidebook_url,
                "description": payload.description,
                "target_role_id": payload.target_role_id,
                "reminders_sent": [],
                "now_utc": now_utc,
            },
        )
        await session.commit()
        row = res.mappings().first()
        return CompetitionRead.model_validate(dict(row))


async def list_active_competitions(guild_id: int) -> list[CompetitionRead]:
    """Retrieves all active competitions for a guild ordered by deadline using raw SQL."""
    async with async_session() as session:
        select_sql = text("""
            SELECT id, guild_id, name, category, deadline, channel_id, created_by,
                   registration_url, guidebook_url, description, target_role_id,
                   reminders_sent, is_active, created_at
            FROM competitions
            WHERE guild_id = :guild_id AND is_active = TRUE
            ORDER BY deadline ASC
        """)
        result = await session.execute(select_sql, {"guild_id": guild_id})
        rows = result.mappings().all()
        return [CompetitionRead.model_validate(dict(r)) for r in rows]


async def get_competition_by_id(comp_id: int, guild_id: int) -> CompetitionRead | None:
    """Retrieves a single active competition by ID using raw SQL."""
    async with async_session() as session:
        select_sql = text("""
            SELECT id, guild_id, name, category, deadline, channel_id, created_by,
                   registration_url, guidebook_url, description, target_role_id,
                   reminders_sent, is_active, created_at
            FROM competitions
            WHERE id = :comp_id AND guild_id = :guild_id
            LIMIT 1
        """)
        result = await session.execute(
            select_sql, {"comp_id": comp_id, "guild_id": guild_id}
        )
        row = result.mappings().first()
        return CompetitionRead.model_validate(dict(row)) if row else None


async def delete_competition(comp_id: int, guild_id: int) -> bool:
    """Soft deletes/deactivates a competition using raw SQL."""
    async with async_session() as session:
        update_sql = text("""
            UPDATE competitions
            SET is_active = FALSE
            WHERE id = :comp_id AND guild_id = :guild_id
        """)
        res = await session.execute(
            update_sql, {"comp_id": comp_id, "guild_id": guild_id}
        )
        await session.commit()
        return res.rowcount > 0


async def update_competition_reminders(comp_id: int, reminders_sent: list[int]) -> None:
    """Updates competition reminder timestamps using raw SQL with JSON parameter binding."""
    async with async_session() as session:
        stmt = text("""
            UPDATE competitions
            SET reminders_sent = :reminders_sent
            WHERE id = :comp_id
        """).bindparams(bindparam("reminders_sent", type_=JSON))

        await session.execute(
            stmt,
            {
                "reminders_sent": reminders_sent,
                "comp_id": comp_id,
            },
        )
        await session.commit()
