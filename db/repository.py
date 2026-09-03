import asyncio
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import logging
import os
import uuid
from uuid import UUID

import aiohttp
from sqlalchemy import text

from db.models import Conversation, MessageRole
from db.schemas import LLMMessagePayload, MessageCreate, MessageRead
from db.session import async_session

logger = logging.getLogger("chat_repository")

# ---------------------------------------------------------
# CONSTANTS & TOKEN BUDGETS (Gemma 4 E2B - 8,192 Tokens Context)
# ---------------------------------------------------------
LLAMA_SERVER_URL = os.environ.get(
    "LLAMA_SERVER_URL", "http://localhost:8080/v1/chat/completions"
)
LLAMA_TOKENIZE_URL = os.environ.get(
    "LLAMA_TOKENIZE_URL",
    LLAMA_SERVER_URL.replace("/v1/chat/completions", "/tokenize"),
)
LLAMA_API_KEY = os.environ.get("LLAMA_API_KEY", "")

# ---------------------------------------------------------
# DYNAMIC TOKEN BUDGETING (Gemma 4 E2B - 8,192 Tokens Context)
# ---------------------------------------------------------
TOTAL_CONTEXT_WINDOW = int(os.environ.get("TOTAL_CONTEXT_WINDOW", "8192"))
MAX_COMPLETION_TOKENS = 1024  # Sesuai max_tokens di ai_client
BASE_OVERHEAD_TOKENS = 1400  # System prompt + Pydantic tools + metadata WIB
TOOL_BUFFER_TOKENS = 1200  # Buffer aman untuk output eksekusi multi-tool paralel

# Sisa kuota aman yang dialokasikan khusus untuk riwayat obrolan (History Budget):
USABLE_HISTORY_BUDGET = max(
    1000,
    TOTAL_CONTEXT_WINDOW
    - (MAX_COMPLETION_TOKENS + BASE_OVERHEAD_TOKENS + TOOL_BUFFER_TOKENS),
)

# Ambang batas pemicu perangkuman riwayat pesan (100% dari budget riwayat, ~55% total context):
COMPACTION_THRESHOLD = int(USABLE_HISTORY_BUDGET)
# Target sisa token riwayat aktif yang dipertahankan setelah perangkuman (~40% dari budget riwayat):
TARGET_RETAIN_TOKENS = int(USABLE_HISTORY_BUDGET * 0.40)

# 24-Hour Sliding TTL for Inactive Conversation Context
CONVERSATION_TTL = timedelta(hours=24)

# ---------------------------------------------------------
# TRUE LRU TOKEN CACHE & PERSISTENT SESSION
# ---------------------------------------------------------
_TOKEN_CACHE: OrderedDict[str, int] = OrderedDict()
_MAX_CACHE_SIZE = 1000
_SHARED_SESSION: aiohttp.ClientSession | None = None
_INFLIGHT_TOKEN_REQUESTS: dict[str, asyncio.Future[int]] = {}


async def get_http_session() -> aiohttp.ClientSession:
    """Get or create persistent aiohttp client session for tokenizing."""
    global _SHARED_SESSION
    if _SHARED_SESSION is None or _SHARED_SESSION.closed:
        _SHARED_SESSION = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=2.0)
        )
    return _SHARED_SESSION


async def close_http_session() -> None:
    """Closes persistent aiohttp session cleanly on bot shutdown."""
    global _SHARED_SESSION
    if _SHARED_SESSION is not None and not _SHARED_SESSION.closed:
        await _SHARED_SESSION.close()
        _SHARED_SESSION = None
        logger.info("Closed persistent aiohttp token session.")


async def count_token(
    text_content: str, session_http: aiohttp.ClientSession | None = None
) -> int:
    """
    True LRU token caching for llama.cpp /tokenize endpoint:
    1. Returns 0 for empty text.
    2. Generates MD5 hash of input text.
    3. Checks _TOKEN_CACHE and calls move_to_end() on cache hit.
    4. Implements single-flight de-duplication for concurrent identical requests.
    5. Falls back to estimation max(1, len(text) // 4) on failure.
    6. Evicts oldest item popitem(last=False) when cache exceeds 1000 entries.
    """
    if not text_content:
        return 0

    text_hash = hashlib.md5(
        text_content.encode("utf-8"), usedforsecurity=False
    ).hexdigest()

    # 1. Cache Hit
    if text_hash in _TOKEN_CACHE:
        _TOKEN_CACHE.move_to_end(text_hash)
        return _TOKEN_CACHE[text_hash]

    # 2. Check Single-Flight in-flight requests
    if text_hash in _INFLIGHT_TOKEN_REQUESTS:
        return await _INFLIGHT_TOKEN_REQUESTS[text_hash]

    # 3. Create Future for in-flight request
    loop = asyncio.get_running_loop()
    future: asyncio.Future[int] = loop.create_future()
    _INFLIGHT_TOKEN_REQUESTS[text_hash] = future

    token_count = 0
    try:
        sess = session_http if session_http is not None else await get_http_session()
        headers = {}
        if LLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {LLAMA_API_KEY}"
        async with sess.post(
            LLAMA_TOKENIZE_URL, json={"content": text_content}, headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                tokens = data.get("tokens", [])
                token_count = len(tokens)
            else:
                token_count = max(1, len(text_content) // 4)
    except Exception:
        # Fallback estimation if tokenize endpoint offline or fails
        token_count = max(1, len(text_content) // 4)
    finally:
        if not future.done():
            future.set_result(token_count)
        _INFLIGHT_TOKEN_REQUESTS.pop(text_hash, None)

    # 4. Insert into LRU Cache
    if len(_TOKEN_CACHE) >= _MAX_CACHE_SIZE:
        _TOKEN_CACHE.popitem(last=False)

    _TOKEN_CACHE[text_hash] = token_count
    return token_count


# ---------------------------------------------------------
# RAW SQL CONVERSATION & CONTEXT REPOSITORY FUNCTIONS
# ---------------------------------------------------------
async def get_or_create_conversation(
    user_id: int, channel_id: int | None = None
) -> Conversation:
    """
    Getting an active conversation based on user_id or creating a new one using raw SQL.
    Implements 24-hour sliding TTL expiration for inactive conversations.
    """
    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        select_sql = text("""
            SELECT id, user_id, channel_id, summary, created_at, updated_at
            FROM conversations
            WHERE user_id = :user_id
            LIMIT 1
        """)
        result = await session.execute(select_sql, {"user_id": user_id})
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
            conv = Conversation(
                id=created_row["id"],
                user_id=created_row["user_id"],
                channel_id=created_row["channel_id"],
                summary=created_row["summary"],
                created_at=created_row["created_at"],
                updated_at=created_row["updated_at"],
            )
            conv.messages = []
            return conv

        conv_id = row["id"]
        last_activity = row["updated_at"]
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

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
                        SET summary = NULL, updated_at = :now_utc, channel_id = COALESCE(:channel_id, channel_id)
                        WHERE id = :conv_id
                    """),
                    {
                        "now_utc": now_utc,
                        "channel_id": channel_id,
                        "conv_id": conv_id,
                    },
                )
                await session.commit()
                conv = Conversation(
                    id=conv_id,
                    user_id=row["user_id"],
                    channel_id=channel_id or row["channel_id"],
                    summary=None,
                    created_at=row["created_at"],
                    updated_at=now_utc,
                )
                conv.messages = []
                return conv

        # Active conversation: update last_activity and channel_id
        await session.execute(
            text("""
                UPDATE conversations 
                SET updated_at = :now_utc, channel_id = COALESCE(:channel_id, channel_id)
                WHERE id = :conv_id
            """),
            {
                "now_utc": now_utc,
                "channel_id": channel_id,
                "conv_id": conv_id,
            },
        )
        await session.commit()
        conv = Conversation(
            id=conv_id,
            user_id=row["user_id"],
            channel_id=channel_id or row["channel_id"],
            summary=row["summary"],
            created_at=row["created_at"],
            updated_at=now_utc,
        )
        return conv


async def save_message(
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    token_count: int | None = None,
) -> MessageRead:
    """Validates and saves a new message with incremental token_count and sliding TTL touch to the database using raw SQL."""
    if token_count is None:
        token_count = await count_token(content)

    payload = MessageCreate(role=role, content=content, token_count=token_count)
    now_utc = datetime.now(timezone.utc)
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


async def get_conversation_context(
    user_id: int,
) -> tuple[str | None, list[dict], int]:
    """
    Retrieves conversation context for LLM based on token quota using incremental token counts and raw SQL.
    Returns (summary, list_messages_for_llm, total_conversation_tokens).
    """
    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        conv_sql = text("""
            SELECT id, summary, updated_at
            FROM conversations
            WHERE user_id = :user_id
            LIMIT 1
        """)
        conv_res = await session.execute(conv_sql, {"user_id": user_id})
        conv_row = conv_res.mappings().first()

        if not conv_row:
            return None, [], 0

        conv_id = conv_row["id"]
        last_activity = conv_row["updated_at"]
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

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
        sorted_messages = msgs_res.mappings().all()

        summary = conv_row["summary"]
        if not sorted_messages:
            summary_tokens = await count_token(summary) if summary else 0
            return summary, [], summary_tokens

        message_payloads: list[dict] = []
        current_tokens = 0

        # 1. Summary tokens
        if summary:
            summary_tokens = await count_token(summary)
            current_tokens += summary_tokens

        # 2. Select messages from newest to oldest within threshold
        recent_selected = []
        for msg in reversed(sorted_messages):
            msg_tok = (
                msg["token_count"]
                if msg["token_count"] > 0
                else await count_token(msg["content"])
            )
            if current_tokens + msg_tok <= COMPACTION_THRESHOLD:
                recent_selected.append((msg, msg_tok))
                current_tokens += msg_tok
            else:
                break

        # Chronological order
        recent_selected.reverse()

        for msg, _ in recent_selected:
            raw_role = msg["role"]
            role_str = raw_role.value if hasattr(raw_role, "value") else str(raw_role)
            llm_item = LLMMessagePayload(
                role=role_str,
                content=msg["content"],
            )
            message_payloads.append(llm_item.model_dump())

        logger.info(
            f"Context loaded for user {user_id}: {len(message_payloads)} messages (~{current_tokens} tokens)"
        )
        return summary, message_payloads, current_tokens


async def check_and_trigger_rolling_summary(
    user_id: int,
    ai_client,
    on_compaction_start=None,
    on_compaction_end=None,
):
    """
    Checks total conversation tokens and performs rolling compaction if exceeding COMPACTION_THRESHOLD using raw SQL.
    Supports on_compaction_start and on_compaction_end callbacks for Discord visual indicators.
    """
    async with async_session() as session:
        conv_sql = text("""
            SELECT id, summary
            FROM conversations
            WHERE user_id = :user_id
            LIMIT 1
        """)
        conv_res = await session.execute(conv_sql, {"user_id": user_id})
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
        sorted_messages = msgs_res.mappings().all()

        if not sorted_messages:
            return

        # Calculate total tokens using stored token counts
        msg_tokens = []
        total_tokens = 0
        for msg in sorted_messages:
            t_count = (
                msg["token_count"]
                if msg["token_count"] > 0
                else await count_token(msg["content"])
            )
            msg_tokens.append((msg, t_count))
            total_tokens += t_count

        if total_tokens < COMPACTION_THRESHOLD:
            return

        # Determine messages to retain
        retained_tokens = 0
        split_index = len(sorted_messages)

        for i in range(len(msg_tokens) - 1, -1, -1):
            msg, t_count = msg_tokens[i]
            if retained_tokens + t_count <= TARGET_RETAIN_TOKENS:
                retained_tokens += t_count
                split_index = i
            else:
                break

        to_summarize = sorted_messages[:split_index]
        if not to_summarize:
            return

        # Trigger visual indicator callback if provided
        if callable(on_compaction_start):
            try:
                res = on_compaction_start()
                if inspect.isawaitable(res):
                    await res
            except Exception as cb_err:
                logger.warning(f"Error in on_compaction_start callback: {cb_err}")

        old_dialogue = "\n".join(
            [
                f"{(m['role'].value if hasattr(m['role'], 'value') else str(m['role'])).upper()}: {m['content']}"
                for m in to_summarize
            ]
        )

        previous_summary = (
            f"Previous summary:\n{conv_row['summary']}\n\n"
            if conv_row["summary"]
            else ""
        )

        summarize_prompt = [
            {
                "role": "system",
                "content": (
                    "You're an AI memory summarizer. Your job is to combine and "
                    "summarize the following conversation concisely, clearly, and factually. Focus on names, facts, preferences, "
                    "topics discussed, and important decisions. Don't be long-winded."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{previous_summary}Conversation to summarize:\n{old_dialogue}"
                    "\n\nMake a concise summary of the conversation above:"
                ),
            },
        ]

        try:
            response = await ai_client.chat.completions.create(
                model="local-model",
                messages=summarize_prompt,
                max_tokens=400,
                temperature=0.3,
            )
            new_summary = response.choices[0].message.content.strip()

            to_delete_ids = [m["id"] for m in to_summarize]
            update_summary_sql = text("""
                UPDATE conversations
                SET summary = :summary
                WHERE id = :conv_id
            """)
            await session.execute(
                update_summary_sql,
                {"summary": new_summary, "conv_id": conv_id},
            )

            delete_msgs_sql = text("""
                DELETE FROM messages
                WHERE id = ANY(:delete_ids)
            """)
            await session.execute(
                delete_msgs_sql,
                {"delete_ids": to_delete_ids},
            )

            await session.commit()
            logger.info(
                f"Rolling summary completed for user {user_id}. "
                f"Summarized & purged {len(to_summarize)} messages (~{total_tokens - retained_tokens} tokens saved)."
            )

        except Exception as e:
            logger.error(f"Failed to execute rolling summary for user {user_id}: {e}")
        finally:
            if callable(on_compaction_end):
                try:
                    res = on_compaction_end()
                    if inspect.isawaitable(res):
                        await res
                except Exception as cb_err:
                    logger.warning(f"Error in on_compaction_end callback: {cb_err}")


async def reset_conversation_history(user_id: int):
    """Deleting entire conversation and user summary (command $reset / /reset) using raw SQL."""
    async with async_session() as session:
        delete_sql = text("""
            DELETE FROM conversations
            WHERE user_id = :user_id
        """)
        await session.execute(delete_sql, {"user_id": user_id})
        await session.commit()
        logger.info(f"Reset conversation history for user {user_id}")


# ---------------------------------------------------------
# RAW SQL TOKEN USAGE ANALYTICS FUNCTIONS
# ---------------------------------------------------------
async def log_token_usage(
    guild_id: int | None,
    user_id: int,
    username: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    latency_ms: int,
) -> None:
    """Stores token usage and latency asynchronously in PostgreSQL using raw SQL."""
    try:
        now_utc = datetime.now(timezone.utc)
        async with async_session() as session:
            insert_sql = text("""
                INSERT INTO token_usage_logs (
                    guild_id, user_id, username, prompt_tokens, completion_tokens, total_tokens, latency_ms, created_at
                )
                VALUES (
                    :guild_id, :user_id, :username, :prompt_tokens, :completion_tokens, :total_tokens, :latency_ms, :now_utc
                )
            """)
            await session.execute(
                insert_sql,
                {
                    "guild_id": guild_id,
                    "user_id": user_id,
                    "username": username,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "latency_ms": latency_ms,
                    "now_utc": now_utc,
                },
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save token usage log: {e}")


async def get_user_token_stats(user_id: int) -> dict:
    """Aggregates user token statistics directly in SQL using raw SQL."""
    async with async_session() as session:
        stats_sql = text("""
            SELECT 
                COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COUNT(id) AS interactions,
                COALESCE(MAX(username), 'User') AS username
            FROM token_usage_logs
            WHERE user_id = :user_id
        """)
        result = await session.execute(stats_sql, {"user_id": user_id})
        row = result.mappings().first()

        if not row or row["interactions"] == 0:
            return {
                "user_id": user_id,
                "username": "User",
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "interactions": 0,
                "avg_tokens_per_interaction": 0.0,
            }

        prompt_tok = int(row["prompt_tokens"])
        comp_tok = int(row["completion_tokens"])
        total_tok = int(row["total_tokens"])
        interactions = int(row["interactions"])
        avg_tok = round(total_tok / interactions, 2) if interactions > 0 else 0.0

        return {
            "user_id": user_id,
            "username": row["username"],
            "total_prompt_tokens": prompt_tok,
            "total_completion_tokens": comp_tok,
            "total_tokens": total_tok,
            "interactions": interactions,
            "avg_tokens_per_interaction": avg_tok,
        }


async def get_guild_token_leaderboard(
    guild_id: int, limit: int = 10
) -> tuple[list[dict], dict]:
    """Returns top 10 token consumers in a guild and guild total usage (aggregated via raw SQL)."""
    async with async_session() as session:
        # Top users in guild
        leaderboard_sql = text("""
            SELECT 
                user_id,
                COALESCE(MAX(username), 'User') AS username,
                COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COUNT(id) AS interactions
            FROM token_usage_logs
            WHERE guild_id = :guild_id
            GROUP BY user_id
            ORDER BY SUM(total_tokens) DESC
            LIMIT :limit
        """)
        result = await session.execute(
            leaderboard_sql, {"guild_id": guild_id, "limit": limit}
        )
        rows = result.mappings().all()
        leaderboard = [
            {
                "user_id": int(r["user_id"]),
                "username": r["username"],
                "prompt_tokens": int(r["prompt_tokens"]),
                "completion_tokens": int(r["completion_tokens"]),
                "total_tokens": int(r["total_tokens"]),
                "interactions": int(r["interactions"]),
            }
            for r in rows
        ]

        # Guild total aggregates
        total_sql = text("""
            SELECT 
                COALESCE(SUM(prompt_tokens), 0) AS guild_prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS guild_completion_tokens,
                COALESCE(SUM(total_tokens), 0) AS guild_total_tokens,
                COUNT(id) AS guild_interactions
            FROM token_usage_logs
            WHERE guild_id = :guild_id
        """)
        total_res = await session.execute(total_sql, {"guild_id": guild_id})
        tot_row = total_res.mappings().first()
        guild_summary = {
            "guild_prompt_tokens": int(tot_row["guild_prompt_tokens"])
            if tot_row
            else 0,
            "guild_completion_tokens": int(tot_row["guild_completion_tokens"])
            if tot_row
            else 0,
            "guild_total_tokens": int(tot_row["guild_total_tokens"]) if tot_row else 0,
            "guild_interactions": int(tot_row["guild_interactions"]) if tot_row else 0,
        }

        return leaderboard, guild_summary
