import logging
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import text

from db.models import MessageRole
from db.schemas.conversation import ConversationRead, MessageCreate, MessageRead
from db.session import async_session

logger = logging.getLogger("chat_repository")
CONVERSATION_TTL = timedelta(hours=24)


async def get_or_create_conversation(
    user_id: int, channel_id: int | None = None
) -> ConversationRead:
    """
    Getting an active conversation based on user_id or creating a new one using raw SQL.
    Implements 24-hour sliding TTL expiration for inactive conversations.
    """
    now_utc = datetime.now(UTC)
    async with async_session() as session:
        select_sql = text("""
            SELECT id, user_id, channel_id, summary, created_at, updated_at
            FROM conversations
            WHERE user_id = :user_id
              AND channel_id IS NOT DISTINCT FROM :channel_id
            LIMIT 1
        """)
        result = await session.execute(
            select_sql, {"user_id": user_id, "channel_id": channel_id}
        )
        row = result.mappings().first()

        if not row:
            new_id = uuid.uuid4()
            insert_sql = text("""
                INSERT INTO conversations (id, user_id, channel_id, created_at, updated_at)
                VALUES (:id, :user_id, :channel_id, :now_utc, :now_utc)
                RETURNING id, user_id, channel_id, summary, created_at, updated_at
            """)
            res = await session.execute(
                insert_sql,
                {
                    "id": new_id,
                    "user_id": user_id,
                    "channel_id": channel_id,
                    "now_utc": now_utc,
                },
            )
            await session.commit()
            created_row = res.mappings().first()
            logger.info(
                f"Created new conversation for user {user_id} (ID: {created_row['id']})"
            )
            return ConversationRead(
                id=created_row["id"],
                user_id=created_row["user_id"],
                channel_id=created_row["channel_id"],
                summary=created_row["summary"],
                created_at=created_row["created_at"],
                updated_at=created_row["updated_at"],
                messages=[],
            )

        conv_id = row["id"]
        last_activity = row["updated_at"]
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=UTC)

            if (now_utc - last_activity) >= CONVERSATION_TTL:
                logger.info(
                    f"Conversation {conv_id} for user {user_id} expired after 24h inactivity. "
                    "Silently clearing history and resetting token counter."
                )
                await session.execute(
                    text("DELETE FROM messages WHERE conversation_id = :conv_id"),
                    {"conv_id": conv_id},
                )
                await session.execute(
                    text("""
                        UPDATE conversations
                        SET summary = NULL, updated_at = :now_utc
                        WHERE id = :conv_id
                    """),
                    {
                        "now_utc": now_utc,
                        "channel_id": channel_id,
                        "conv_id": conv_id,
                    },
                )
                await session.commit()
                return ConversationRead(
                    id=conv_id,
                    user_id=row["user_id"],
                    channel_id=row["channel_id"],
                    summary=None,
                    created_at=row["created_at"],
                    updated_at=now_utc,
                    messages=[],
                )

        # Active conversation: update last_activity for this user/channel pair.
        await session.execute(
            text("""
                UPDATE conversations
                SET updated_at = :now_utc
                WHERE id = :conv_id
            """),
            {
                "now_utc": now_utc,
                "channel_id": channel_id,
                "conv_id": conv_id,
            },
        )
        await session.commit()
        return ConversationRead(
            id=conv_id,
            user_id=row["user_id"],
            channel_id=row["channel_id"],
            summary=row["summary"],
            created_at=row["created_at"],
            updated_at=now_utc,
            messages=[],
        )


async def persist_message(
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    token_count: int,
) -> MessageRead:
    """Validates and saves a new message with incremental token_count and sliding TTL touch to the database using raw SQL."""
    payload = MessageCreate(role=role, content=content, token_count=token_count)
    now_utc = datetime.now(UTC)
    new_msg_id = uuid.uuid4()

    role_val = (
        payload.role.name
        if hasattr(payload.role, "name")
        else str(payload.role).upper()
    )

    async with async_session() as session:
        insert_sql = text("""
            INSERT INTO messages (id, conversation_id, role, content, token_count, created_at)
            VALUES (:id, :conversation_id, :role, :content, :token_count, :now_utc)
            RETURNING id, conversation_id, role, content, token_count, created_at
        """)
        res = await session.execute(
            insert_sql,
            {
                "id": new_msg_id,
                "conversation_id": conversation_id,
                "role": role_val,
                "content": payload.content,
                "token_count": payload.token_count,
                "now_utc": now_utc,
            },
        )

        update_conv_sql = text("""
            UPDATE conversations
            SET updated_at = :now_utc
            WHERE id = :conversation_id
        """)
        await session.execute(
            update_conv_sql,
            {"now_utc": now_utc, "conversation_id": conversation_id},
        )

        await session.commit()
        msg_row = res.mappings().first()
        logger.info(
            f"Message ({role.value}, {payload.token_count} tok) added to conversation {conversation_id}"
        )
        saved_role_raw = msg_row["role"]
        saved_role_enum = (
            MessageRole[saved_role_raw]
            if saved_role_raw in MessageRole.__members__
            else MessageRole(str(saved_role_raw).lower())
        )
        return MessageRead(
            id=msg_row["id"],
            conversation_id=msg_row["conversation_id"],
            role=saved_role_enum,
            content=msg_row["content"],
            token_count=msg_row["token_count"],
            created_at=msg_row["created_at"],
        )


async def reset_conversation_history(user_id: int, channel_id: int | None = None):
    """Delete one user's conversation and summary for the selected channel."""
    async with async_session() as session:
        delete_sql = text("""
            DELETE FROM conversations
            WHERE user_id = :user_id
              AND channel_id IS NOT DISTINCT FROM :channel_id
        """)
        await session.execute(
            delete_sql, {"user_id": user_id, "channel_id": channel_id}
        )
        await session.commit()
        logger.info(f"Reset conversation history for user {user_id}")


async def _with_context_data(user_id: int, channel_id: int | None, consume):
    """Load context rows and consume them while the original read session is open."""
    now_utc = datetime.now(UTC)
    async with async_session() as session:
        conv_sql = text("""
            SELECT id, summary, updated_at
            FROM conversations
            WHERE user_id = :user_id
              AND channel_id IS NOT DISTINCT FROM :channel_id
            LIMIT 1
        """)
        conv_res = await session.execute(
            conv_sql, {"user_id": user_id, "channel_id": channel_id}
        )
        conv_row = conv_res.mappings().first()
        if not conv_row:
            return await consume(None, [])

        conv_id = conv_row["id"]
        last_activity = conv_row["updated_at"]
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=UTC)
            if (now_utc - last_activity) >= CONVERSATION_TTL:
                logger.info(
                    f"Context expired for user {user_id} after 24h inactivity. Returning empty context."
                )
                await session.execute(
                    text("DELETE FROM messages WHERE conversation_id = :conv_id"),
                    {"conv_id": conv_id},
                )
                await session.execute(
                    text(
                        "UPDATE conversations SET summary = NULL, updated_at = :now_utc WHERE id = :conv_id"
                    ),
                    {"now_utc": now_utc, "conv_id": conv_id},
                )
                await session.commit()
                return None, [], 0

        msgs_sql = text("""
            SELECT id, role, content, token_count, created_at
            FROM messages
            WHERE conversation_id = :conv_id
            ORDER BY created_at ASC
        """)
        msgs_res = await session.execute(msgs_sql, {"conv_id": conv_id})
        return await consume(conv_row["summary"], msgs_res.mappings().all())


async def _compact_conversation(user_id: int, channel_id: int | None, compact):
    """Keep query and persistence in the repository while a service compacts rows."""
    async with async_session() as session:
        conv_sql = text("""
            SELECT id, summary
            FROM conversations
            WHERE user_id = :user_id
              AND channel_id IS NOT DISTINCT FROM :channel_id
            LIMIT 1
        """)
        conv_res = await session.execute(
            conv_sql, {"user_id": user_id, "channel_id": channel_id}
        )
        conv_row = conv_res.mappings().first()
        if not conv_row:
            return

        conv_id = conv_row["id"]
        msgs_sql = text("""
            SELECT id, role, content, token_count, created_at
            FROM messages
            WHERE conversation_id = :conv_id
            ORDER BY created_at ASC
        """)
        msgs_res = await session.execute(msgs_sql, {"conv_id": conv_id})
        result = await compact(conv_row, msgs_res.mappings().all())
        if not result:
            return
        new_summary, to_delete_ids = result[:2]
        update_summary_sql = text("""
            UPDATE conversations
            SET summary = :summary
            WHERE id = :conv_id
        """)
        await session.execute(
            update_summary_sql, {"summary": new_summary, "conv_id": conv_id}
        )
        delete_msgs_sql = text("""
            DELETE FROM messages
            WHERE id = ANY(:delete_ids)
        """)
        await session.execute(delete_msgs_sql, {"delete_ids": to_delete_ids})
        await session.commit()
        return result
