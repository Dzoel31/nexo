import os
import logging
from uuid import UUID
import aiohttp
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from db.models import Conversation, Message, MessageRole
from db.schemas import MessageCreate, MessageRead, LLMMessagePayload
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

TOTAL_CONTEXT_WINDOW = 8192
# Ambang batas pemicu perangkuman: jika total token pesan >= 6,144 (75% context window)
COMPACTION_THRESHOLD = int(TOTAL_CONTEXT_WINDOW * 0.75)  # 6144 token
# Target sisa token riwayat aktif yang dipertahankan setelah perangkuman
TARGET_RETAIN_TOKENS = int(TOTAL_CONTEXT_WINDOW * 0.30)  # 2457 token


async def count_token(
    text: str, session_http: aiohttp.ClientSession | None = None
) -> int:
    """
    Counting tokens using llama-server /tokenize endpoint.
    Fallback to character estimation (~4 characters per token) if failed or offline.
    """
    if not text:
        return 0

    try:
        should_close = False
        if session_http is None:
            session_http = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=2.0)
            )
            should_close = True

        try:
            async with session_http.post(
                LLAMA_TOKENIZE_URL, json={"content": text}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tokens = data.get("tokens", [])
                    return len(tokens)
        finally:
            if should_close:
                await session_http.close()

    except Exception:
        # Fallback estimasi kasar jika llama-server tokenize offline
        pass

    return max(1, len(text) // 4)


async def get_or_create_conversation(
    user_id: int, channel_id: int | None = None
) -> Conversation:
    """Getting an active conversation based on user_id or creating a new one if not exists."""
    async with async_session() as session:
        stmt = (
            select(Conversation)
            .filter_by(user_id=user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation:
            conversation = Conversation(user_id=user_id, channel_id=channel_id)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            logger.info(
                f"Created new conversation for user {user_id} (ID: {conversation.id})"
            )

        return conversation


async def save_message(
    conversation_id: UUID,
    role: MessageRole,
    content: str,
) -> MessageRead:
    """Validates with Pydantic and saves a new message (user/assistant) to the database."""
    # 1. Pydantic validation
    payload = MessageCreate(role=role, content=content)

    async with async_session() as session:
        msg = Message(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        logger.info(f"Message ({role.value}) added to conversation {conversation_id}")
        return MessageRead.model_validate(msg)


async def get_conversation_context(
    user_id: int,
) -> tuple[str | None, list[dict]]:
    """
    Retrieves conversation context for LLM based on token quota:
    1. Inserts rolling summary (if any).
    2. Inserts the latest messages that still fit within the token budget.
    Returns (summary, list_messages_for_llm).
    """
    async with async_session() as session:
        stmt = (
            select(Conversation)
            .filter_by(user_id=user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation:
            return None, []

        sorted_messages = sorted(conversation.messages, key=lambda m: m.created_at)
        if not sorted_messages:
            return conversation.summary, []

        message_payloads: list[dict] = []
        current_tokens = 0

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=2.0)
        ) as http_sess:
            # 1. Hitung token summary (prioritas tertinggi)
            if conversation.summary:
                summary_tokens = await count_token(conversation.summary, http_sess)
                current_tokens += summary_tokens

            # 2. Ambil pesan dari yang TERBARU ke yang TERLAMA sampai menyentuh batas budget
            recent_selected = []
            for msg in reversed(sorted_messages):
                msg_token_count = await count_token(msg.content, http_sess)
                if current_tokens + msg_token_count <= COMPACTION_THRESHOLD:
                    recent_selected.append(msg)
                    current_tokens += msg_token_count
                else:
                    break

            # Kembalikan ke urutan kronologis awal (lama -> baru)
            recent_selected.reverse()

            for msg in recent_selected:
                llm_item = LLMMessagePayload(
                    role=msg.role.value,
                    content=msg.content,
                )
                message_payloads.append(llm_item.model_dump())

        logger.info(
            f"Context loaded for user {user_id}: {len(message_payloads)} messages (~{current_tokens} tokens)"
        )
        return conversation.summary, message_payloads


async def check_and_trigger_rolling_summary(user_id: int, ai_client):
    """
    Mengecek total token percakapan di database.
    Jika total token >= COMPACTION_THRESHOLD (6,144 token):
    - Pisahkan pesan lama yang melebihi TARGET_RETAIN_TOKENS.
    - Minta LLM merangkum pesan lama tersebut.
    - Perbarui kolom `summary` dan hapus pesan lama yang telah dirangkum.
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

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=2.0)
        ) as http_sess:
            # Hitung total token seluruh pesan
            msg_tokens = []
            total_tokens = 0
            for msg in sorted_messages:
                t_count = await count_token(msg.content, http_sess)
                msg_tokens.append((msg, t_count))
                total_tokens += t_count

            # Jika belum melewati ambang batas 75% context window, belum perlu perangkuman
            if total_tokens < COMPACTION_THRESHOLD:
                return

            # Tentukan pesan mana yang dipertahankan (dari belakang sampai ~TARGET_RETAIN_TOKENS)
            retained_tokens = 0
            split_index = len(sorted_messages)

            for i in range(len(msg_tokens) - 1, -1, -1):
                msg, t_count = msg_tokens[i]
                if retained_tokens + t_count <= TARGET_RETAIN_TOKENS:
                    retained_tokens += t_count
                    split_index = i
                else:
                    break

            # Pesan sebelum split_index akan dirangkum & dihapus
            to_summarize = sorted_messages[:split_index]
            if not to_summarize:
                return

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
                    model="gemma-4-e2b",
                    messages=summarize_prompt,
                    max_tokens=400,
                    temperature=0.3,
                )
                new_summary = response.choices[0].message.content.strip()

                # Perbarui summary di database
                conversation.summary = new_summary

                # Hapus pesan lama yang sudah terangkum
                to_delete_ids = [m.id for m in to_summarize]
                await session.execute(
                    delete(Message).where(Message.id.in_(to_delete_ids))
                )

                await session.commit()
                logger.info(
                    f"Rolling summary completed for user {user_id}. "
                    f"Summarized & purged {len(to_summarize)} messages (~{total_tokens - retained_tokens} tokens)."
                )

            except Exception as e:
                logger.error(
                    f"Failed to execute rolling summary for user {user_id}: {e}"
                )


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
