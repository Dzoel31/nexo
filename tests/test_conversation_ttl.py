from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import text
from db.models import MessageRole
from db.repository import (
    CONVERSATION_TTL,
    get_conversation_context,
    get_or_create_conversation,
    save_message,
)
from db.session import async_session
from tests.conftest import requires_postgres


@requires_postgres
@pytest.mark.asyncio
async def test_conversation_sliding_ttl():
    test_user_id = 999111222333
    channel_id = 123456789

    # 1. Clean previous test artifacts if any
    async with async_session() as session:
        await session.execute(
            text("DELETE FROM token_usage_logs WHERE user_id = :user_id"),
            {"user_id": test_user_id},
        )
        await session.execute(
            text("DELETE FROM conversations WHERE user_id = :user_id"),
            {"user_id": test_user_id},
        )
        await session.commit()

    try:
        # 2. Create fresh active conversation
        conv = await get_or_create_conversation(test_user_id, channel_id)
        assert conv is not None
        assert conv.user_id == test_user_id

        # 3. Add test messages
        await save_message(conv.id, MessageRole.USER, "Halo Nexo! Tes 1 2 3.")
        await save_message(conv.id, MessageRole.ASSISTANT, "Halo! Nexo siap membantu.")

        # 4. Context within TTL should be active
        summary, messages, total_tokens = await get_conversation_context(test_user_id)
        assert len(messages) == 2
        assert total_tokens > 0

        # 5. Simulate 25 hours of inactivity (> 24h CONVERSATION_TTL)
        past_time = datetime.now(timezone.utc) - (CONVERSATION_TTL + timedelta(hours=1))
        async with async_session() as session:
            await session.execute(
                text(
                    "UPDATE conversations SET updated_at = :past_time WHERE id = :conv_id"
                ),
                {"past_time": past_time, "conv_id": conv.id},
            )
            await session.commit()

        # 6. Context should be automatically reset to 0 tokens / 0 messages
        summary_exp, messages_exp, tokens_exp = await get_conversation_context(
            test_user_id
        )
        assert summary_exp is None
        assert len(messages_exp) == 0
        assert tokens_exp == 0

    finally:
        # Cleanup
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM token_usage_logs WHERE user_id = :user_id"),
                {"user_id": test_user_id},
            )
            await session.execute(
                text("DELETE FROM conversations WHERE user_id = :user_id"),
                {"user_id": test_user_id},
            )
            await session.commit()
