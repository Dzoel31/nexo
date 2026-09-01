import asyncio
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import os
from uuid import UUID

import aiohttp
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from db.models import Conversation, Message, MessageRole, TokenUsageLog
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

TOTAL_CONTEXT_WINDOW = 8448
# Base overhead (System prompt + Sanitized tools) is ~1,400 tokens.
# Ambang batas pemicu perangkuman riwayat pesan: 4,500 token (Total payload aman <= 6,500 < 8,448)
COMPACTION_THRESHOLD = 4500
# Target sisa token riwayat aktif yang dipertahankan setelah perangkuman
TARGET_RETAIN_TOKENS = 1800

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
    text: str, session_http: aiohttp.ClientSession | None = None
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
    if not text:
        return 0

    text_hash = hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()

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
        async with sess.post(LLAMA_TOKENIZE_URL, json={"content": text}) as response:
            if response.status == 200:
                data = await response.json()
                tokens = data.get("tokens", [])
                token_count = len(tokens)
            else:
                token_count = max(1, len(text) // 4)
    except Exception:
        # Fallback estimation if tokenize endpoint offline or fails
        token_count = max(1, len(text) // 4)
    finally:
        if not future.done():
            future.set_result(token_count)
        _INFLIGHT_TOKEN_REQUESTS.pop(text_hash, None)

    # 4. Insert into LRU Cache
    if len(_TOKEN_CACHE) >= _MAX_CACHE_SIZE:
        _TOKEN_CACHE.popitem(last=False)

    _TOKEN_CACHE[text_hash] = token_count
    return token_count


async def get_or_create_conversation(
    user_id: int, channel_id: int | None = None
) -> Conversation:
    """
    Getting an active conversation based on user_id or creating a new one.
    Implements 24-hour sliding TTL expiration for inactive conversations.
    """
    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        stmt = (
            select(Conversation)
            .filter_by(user_id=user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation:
            conversation = Conversation(
                user_id=user_id,
                channel_id=channel_id,
                created_at=now_utc,
                updated_at=now_utc,
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            logger.info(
                f"Created new conversation for user {user_id} (ID: {conversation.id})"
            )
            return conversation

        # Check 24-hour sliding TTL
        last_activity = conversation.updated_at
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            if (now_utc - last_activity) >= CONVERSATION_TTL:
                logger.info(
                    f"Conversation {conversation.id} for user {user_id} expired after 24h inactivity. "
                    "Silently clearing history and resetting token counter."
                )
                await session.execute(
                    delete(Message).where(Message.conversation_id == conversation.id)
                )
                conversation.summary = None
                conversation.messages = []
                conversation.updated_at = now_utc
                if channel_id:
                    conversation.channel_id = channel_id
                await session.commit()
                await session.refresh(conversation)
                return conversation

        # Update last activity timestamp on active conversation
        conversation.updated_at = now_utc
        if channel_id:
            conversation.channel_id = channel_id
        await session.commit()
        await session.refresh(conversation)
        return conversation


async def save_message(
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    token_count: int | None = None,
) -> MessageRead:
    """Validates and saves a new message with incremental token_count and sliding TTL touch to the database."""
    if token_count is None:
        token_count = await count_token(content)

    payload = MessageCreate(role=role, content=content, token_count=token_count)

    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        msg = Message(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
            token_count=payload.token_count,
        )
        session.add(msg)

        # Update conversation updated_at for sliding TTL
        conv_stmt = select(Conversation).filter_by(id=conversation_id)
        conv_res = await session.execute(conv_stmt)
        conv = conv_res.scalars().first()
        if conv:
            conv.updated_at = now_utc

        await session.commit()
        await session.refresh(msg)
        logger.info(
            f"Message ({role.value}, {payload.token_count} tok) added to conversation {conversation_id}"
        )
        return MessageRead.model_validate(msg)


async def get_conversation_context(
    user_id: int,
) -> tuple[str | None, list[dict], int]:
    """
    Retrieves conversation context for LLM based on token quota using incremental token counts.
    Returns (summary, list_messages_for_llm, total_conversation_tokens).
    """
    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        stmt = (
            select(Conversation)
            .filter_by(user_id=user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation:
            return None, [], 0

        # Check 24-hour sliding TTL
        last_activity = conversation.updated_at
        if last_activity:
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)

            if (now_utc - last_activity) >= CONVERSATION_TTL:
                logger.info(
                    f"Context expired for user {user_id} after 24h inactivity. Returning empty context."
                )
                await session.execute(
                    delete(Message).where(Message.conversation_id == conversation.id)
                )
                conversation.summary = None
                conversation.messages = []
                conversation.updated_at = now_utc
                await session.commit()
                return None, [], 0

        sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)
        if not sorted_messages:
            summary_tokens = (
                await count_token(conversation.summary) if conversation.summary else 0
            )
            return conversation.summary, [], summary_tokens

        message_payloads: list[dict] = []
        current_tokens = 0

        # 1. Summary tokens
        if conversation.summary:
            summary_tokens = await count_token(conversation.summary)
            current_tokens += summary_tokens

        # 2. Select messages from newest to oldest within threshold
        recent_selected = []
        for msg in reversed(sorted_messages):
            msg_tok = (
                msg.token_count
                if msg.token_count > 0
                else await count_token(msg.content)
            )
            if current_tokens + msg_tok <= COMPACTION_THRESHOLD:
                recent_selected.append((msg, msg_tok))
                current_tokens += msg_tok
            else:
                break

        # Chronological order
        recent_selected.reverse()

        for msg, _ in recent_selected:
            llm_item = LLMMessagePayload(
                role=msg.role.value,
                content=msg.content,
            )
            message_payloads.append(llm_item.model_dump())

        logger.info(
            f"Context loaded for user {user_id}: {len(message_payloads)} messages (~{current_tokens} tokens)"
        )
        return conversation.summary, message_payloads, current_tokens


async def check_and_trigger_rolling_summary(
    user_id: int,
    ai_client,
    on_compaction_start=None,
    on_compaction_end=None,
):
    """
    Checks total conversation tokens and performs rolling compaction if exceeding COMPACTION_THRESHOLD.
    Supports on_compaction_start and on_compaction_end callbacks for Discord visual indicators.
    """
    async with async_session() as session:
        stmt = (
            select(Conversation)
            .filter_by(user_id=user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation or not conversation.messages:
            return

        sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)

        # Calculate total tokens using stored token counts
        msg_tokens = []
        total_tokens = 0
        for msg in sorted_messages:
            t_count = (
                msg.token_count
                if msg.token_count > 0
                else await count_token(msg.content)
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
                if asyncio.iscoroutine(res):
                    await res
            except Exception as cb_err:
                logger.warning(f"Error in on_compaction_start callback: {cb_err}")

        old_dialogue = "\n".join(
            [f"{m.role.value.upper()}: {m.content}" for m in to_summarize]
        )

        previous_summary = (
            f"Previous summary:\n{conversation.summary}\n\n"
            if conversation.summary
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

            conversation.summary = new_summary

            to_delete_ids = [m.id for m in to_summarize]
            await session.execute(delete(Message).where(Message.id.in_(to_delete_ids)))

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
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as cb_err:
                    logger.warning(f"Error in on_compaction_end callback: {cb_err}")


async def reset_conversation_history(user_id: int):
    """Deleting entire conversation and user summary (command $reset / /reset)."""
    async with async_session() as session:
        stmt = select(Conversation).filter_by(user_id=user_id)
        result = await session.execute(stmt)
        conversation = result.scalars().first()
        if conversation:
            await session.delete(conversation)
            await session.commit()
            logger.info(f"Reset conversation history for user {user_id}")


# ---------------------------------------------------------
# TOKEN USAGE ANALYTICS REPOSITORY FUNCTIONS
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
    """Stores token usage and latency asynchronously in PostgreSQL."""
    try:
        async with async_session() as session:
            entry = TokenUsageLog(
                guild_id=guild_id,
                user_id=user_id,
                username=username,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
            )
            session.add(entry)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to save token usage log: {e}")


async def get_user_token_stats(user_id: int) -> dict:
    """Aggregates user token statistics directly in SQL."""
    async with async_session() as session:
        stmt = select(
            func.coalesce(func.sum(TokenUsageLog.prompt_tokens), 0).label(
                "prompt_tokens"
            ),
            func.coalesce(func.sum(TokenUsageLog.completion_tokens), 0).label(
                "completion_tokens"
            ),
            func.coalesce(func.sum(TokenUsageLog.total_tokens), 0).label(
                "total_tokens"
            ),
            func.count(TokenUsageLog.id).label("interactions"),
            func.coalesce(func.max(TokenUsageLog.username), "User").label("username"),
        ).where(TokenUsageLog.user_id == user_id)

        result = await session.execute(stmt)
        row = result.first()
        if not row or row.interactions == 0:
            return {
                "user_id": user_id,
                "username": "User",
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "interactions": 0,
                "avg_tokens_per_interaction": 0.0,
            }

        prompt_tok = int(row.prompt_tokens)
        comp_tok = int(row.completion_tokens)
        total_tok = int(row.total_tokens)
        interactions = int(row.interactions)
        avg_tok = round(total_tok / interactions, 2) if interactions > 0 else 0.0

        return {
            "user_id": user_id,
            "username": row.username,
            "total_prompt_tokens": prompt_tok,
            "total_completion_tokens": comp_tok,
            "total_tokens": total_tok,
            "interactions": interactions,
            "avg_tokens_per_interaction": avg_tok,
        }


async def get_guild_token_leaderboard(
    guild_id: int, limit: int = 10
) -> tuple[list[dict], dict]:
    """Returns top 10 token consumers in a guild and guild total usage (aggregated in SQL)."""
    async with async_session() as session:
        # Top 10 users in guild
        stmt = (
            select(
                TokenUsageLog.user_id,
                func.max(TokenUsageLog.username).label("username"),
                func.sum(TokenUsageLog.prompt_tokens).label("prompt_tokens"),
                func.sum(TokenUsageLog.completion_tokens).label("completion_tokens"),
                func.sum(TokenUsageLog.total_tokens).label("total_tokens"),
                func.count(TokenUsageLog.id).label("interactions"),
            )
            .where(TokenUsageLog.guild_id == guild_id)
            .group_by(TokenUsageLog.user_id)
            .order_by(func.sum(TokenUsageLog.total_tokens).desc())
            .limit(limit)
        )

        result = await session.execute(stmt)
        rows = result.all()
        leaderboard = [
            {
                "user_id": int(r.user_id),
                "username": r.username,
                "prompt_tokens": int(r.prompt_tokens or 0),
                "completion_tokens": int(r.completion_tokens or 0),
                "total_tokens": int(r.total_tokens or 0),
                "interactions": int(r.interactions or 0),
            }
            for r in rows
        ]

        # Guild total aggregates
        total_stmt = select(
            func.coalesce(func.sum(TokenUsageLog.prompt_tokens), 0).label(
                "guild_prompt_tokens"
            ),
            func.coalesce(func.sum(TokenUsageLog.completion_tokens), 0).label(
                "guild_completion_tokens"
            ),
            func.coalesce(func.sum(TokenUsageLog.total_tokens), 0).label(
                "guild_total_tokens"
            ),
            func.count(TokenUsageLog.id).label("guild_interactions"),
        ).where(TokenUsageLog.guild_id == guild_id)

        total_res = await session.execute(total_stmt)
        tot_row = total_res.first()
        guild_summary = {
            "guild_prompt_tokens": int(tot_row.guild_prompt_tokens or 0)
            if tot_row
            else 0,
            "guild_completion_tokens": int(tot_row.guild_completion_tokens or 0)
            if tot_row
            else 0,
            "guild_total_tokens": int(tot_row.guild_total_tokens or 0)
            if tot_row
            else 0,
            "guild_interactions": int(tot_row.guild_interactions or 0)
            if tot_row
            else 0,
        }

        return leaderboard, guild_summary
