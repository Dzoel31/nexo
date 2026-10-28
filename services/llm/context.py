"""LLM conversation context selection and rolling summary orchestration."""

import inspect
import logging
from uuid import UUID

from db.models import MessageRole
from db.repositories.conversation import (
    _compact_conversation,
    _with_context_data,
    persist_message,
)
from schemas.llm.conversation import LLMMessagePayload
from services.llm.token_counter import (
    COMPACTION_THRESHOLD,
    TARGET_RETAIN_TOKENS,
    count_token,
)

logger = logging.getLogger("chat_repository")


async def save_message(
    conversation_id: UUID,
    role: MessageRole,
    content: str,
    token_count: int | None = None,
):
    """Count tokens when needed, then persist a conversation message."""
    if token_count is None:
        token_count = await count_token(content)
    return await persist_message(conversation_id, role, content, token_count)


async def get_conversation_context(user_id: int) -> tuple[str | None, list[dict], int]:
    """Build a token-budgeted LLM context from persisted conversation rows."""

    async def build_context(summary, sorted_messages):
        if summary is None and not sorted_messages:
            return None, [], 0
        if not sorted_messages:
            return summary, [], await count_token(summary) if summary else 0
        current_tokens = 0
        if summary:
            current_tokens += await count_token(summary)
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
        recent_selected.reverse()
        payloads = []
        for msg, _ in recent_selected:
            raw_role = msg["role"]
            role_str = (
                raw_role.value if hasattr(raw_role, "value") else str(raw_role)
            ).lower()
            if role_str not in {"system", "user", "assistant", "tool"}:
                raise ValueError(f"Unsupported persisted message role: {raw_role!r}")
            payloads.append(
                LLMMessagePayload(role=role_str, content=msg["content"]).model_dump()
            )
        logger.info(
            "Context loaded for user %s: %s messages (~%s tokens)",
            user_id,
            len(payloads),
            current_tokens,
        )
        return summary, payloads, current_tokens

    return await _with_context_data(user_id, build_context)


async def check_and_trigger_rolling_summary(
    user_id: int, ai_client, on_compaction_start=None, on_compaction_end=None
):
    """Compact old conversation messages and persist the generated rolling summary."""
    end_callback_required = False

    async def compact(conv_row, sorted_messages):
        nonlocal end_callback_required
        if not sorted_messages:
            return None
        msg_tokens = []
        total_tokens = 0
        for msg in sorted_messages:
            token_total = (
                msg["token_count"]
                if msg["token_count"] > 0
                else await count_token(msg["content"])
            )
            msg_tokens.append((msg, token_total))
            total_tokens += token_total
        if total_tokens < COMPACTION_THRESHOLD:
            return None
        retained_tokens = 0
        split_index = len(sorted_messages)
        for i in range(len(msg_tokens) - 1, -1, -1):
            _, token_total = msg_tokens[i]
            if retained_tokens + token_total <= TARGET_RETAIN_TOKENS:
                retained_tokens += token_total
                split_index = i
            else:
                break
        to_summarize = sorted_messages[:split_index]
        if not to_summarize:
            return None
        if callable(on_compaction_start):
            try:
                result = on_compaction_start()
                if inspect.isawaitable(result):
                    await result
            except Exception as cb_err:  # noqa: BLE001
                logger.warning("Error in on_compaction_start callback: %s", cb_err)
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
                "content": "You're an AI memory summarizer. Your job is to combine and summarize the following conversation concisely, clearly, and factually. Focus on names, facts, preferences, topics discussed, and important decisions. Don't be long-winded.",
            },
            {
                "role": "user",
                "content": f"{previous_summary}Conversation to summarize:\n{old_dialogue}\n\nMake a concise summary of the conversation above:",
            },
        ]
        end_callback_required = True
        try:
            response = await ai_client.chat.completions.create(
                model="local-model",
                messages=summarize_prompt,
                max_completion_tokens=400,
                temperature=0.3,
            )
            new_summary = response.choices[0].message.content.strip()
            to_delete_ids = [message["id"] for message in to_summarize]
            return (
                new_summary,
                to_delete_ids,
                len(to_summarize),
                total_tokens - retained_tokens,
            )
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Failed to execute rolling summary for user %s: %s", user_id, error
            )
            return None

    try:
        result = await _compact_conversation(user_id, compact)
        if result:
            logger.info(
                "Rolling summary completed for user %s. Summarized & purged %s messages (~%s tokens saved).",
                user_id,
                result[2],
                result[3],
            )
    except Exception as error:  # noqa: BLE001
        logger.error(
            "Failed to execute rolling summary for user %s: %s", user_id, error
        )
    finally:
        if end_callback_required and callable(on_compaction_end):
            try:
                result = on_compaction_end()
                if inspect.isawaitable(result):
                    await result
            except Exception as cb_err:  # noqa: BLE001
                logger.warning("Error in on_compaction_end callback: %s", cb_err)
