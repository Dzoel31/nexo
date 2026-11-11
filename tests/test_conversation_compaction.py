from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config.settings import settings
from db.models import MessageRole
from services.llm import context


@pytest.mark.asyncio
async def test_rolling_summary_uses_configured_inference_model(monkeypatch):
    messages = [
        {
            "id": "user-message",
            "role": MessageRole.USER,
            "content": "A user message.",
            "token_count": 2,
        },
        {
            "id": "assistant-message",
            "role": MessageRole.ASSISTANT,
            "content": "An assistant response.",
            "token_count": 2,
        },
    ]
    monkeypatch.setattr(
        context,
        "get_context_budget",
        AsyncMock(return_value=(8192, 3, 1)),
    )

    async def compact_conversation(_user_id, _channel_id, compact):
        return await compact({"summary": None}, messages)

    monkeypatch.setattr(context, "_compact_conversation", compact_conversation)
    create = AsyncMock(
        return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Summary."))]
        )
    )
    ai_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    await context.check_and_trigger_rolling_summary(
        user_id=123,
        ai_client=ai_client,
        channel_id=456,
    )

    assert create.await_args.kwargs["model"] == settings.LLM_MODEL_NAME
