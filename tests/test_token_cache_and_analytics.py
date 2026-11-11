import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text

from db.repositories.token_usage import (
    get_guild_token_leaderboard,
    get_user_token_stats,
    log_token_usage,
)
from db.session import async_session
from services.llm import token_counter
from services.llm.token_counter import count_token
from tests.conftest import requires_postgres


def test_parse_litellm_metadata_for_configured_model():
    payload = {
        "data": [
            {
                "model_name": "other-model",
                "litellm_params": {"tokenizer_with_hf_repo": "other/tokenizer"},
                "model_info": {"max_input_tokens": 4096},
            },
            {
                "model_name": "active-model",
                "litellm_params": {"tokenizer_with_hf_repo": "google/gemma-it"},
                "model_info": {"max_input_tokens": 8192},
            },
        ]
    }

    assert token_counter.parse_litellm_model_metadata(payload, "active-model") == (
        "google/gemma-it",
        8192,
    )


@pytest.mark.asyncio
async def test_context_budget_uses_resolved_model_limit_without_minimum_floor(
    monkeypatch,
):
    monkeypatch.setattr(token_counter, "_resolve_model_metadata", AsyncMock())
    monkeypatch.setattr(token_counter, "_RESOLVED_CONTEXT_WINDOW", 2048)

    (
        context_window,
        history_budget,
        retained_budget,
    ) = await token_counter.get_context_budget(prompt_overhead_tokens=500)

    assert context_window == 2048
    assert history_budget == 0
    assert retained_budget == 0


@pytest.mark.asyncio
async def test_context_budget_never_exceeds_configured_total_limit(monkeypatch):
    monkeypatch.setattr(token_counter, "_resolve_model_metadata", AsyncMock())
    monkeypatch.setattr(token_counter, "_RESOLVED_CONTEXT_WINDOW", 16384)
    monkeypatch.setattr(token_counter, "TOTAL_CONTEXT_WINDOW", 8192)

    context_window, _, _ = await token_counter.get_context_budget(
        prompt_overhead_tokens=500
    )

    assert context_window == 8192


@pytest.mark.asyncio
async def test_context_budget_uses_configured_limit_when_metadata_is_missing(
    monkeypatch,
):
    monkeypatch.setattr(token_counter, "_resolve_model_metadata", AsyncMock())
    monkeypatch.setattr(token_counter, "_RESOLVED_CONTEXT_WINDOW", None)
    monkeypatch.setattr(token_counter, "TOTAL_CONTEXT_WINDOW", 8192)

    context_window, _, _ = await token_counter.get_context_budget(
        prompt_overhead_tokens=500
    )

    assert context_window == 8192


@pytest.mark.asyncio
async def test_context_budget_includes_observed_estimation_margin(monkeypatch):
    monkeypatch.setattr(token_counter, "_resolve_model_metadata", AsyncMock())
    monkeypatch.setattr(token_counter, "_RESOLVED_CONTEXT_WINDOW", 8192)
    monkeypatch.setattr(token_counter, "_PROMPT_ESTIMATE_SAFETY_MARGIN", 200)

    _, history_budget, _ = await token_counter.get_context_budget(500)

    assert history_budget == 5268


def test_prompt_estimation_margin_waits_for_enough_samples(monkeypatch):
    monkeypatch.setattr(
        token_counter,
        "_PROMPT_ESTIMATE_GAPS",
        token_counter.deque(maxlen=token_counter.PROMPT_ESTIMATE_HISTORY_SIZE),
    )
    monkeypatch.setattr(token_counter, "_PROMPT_ESTIMATE_SAFETY_MARGIN", 128)

    for _ in range(token_counter.PROMPT_ESTIMATE_MIN_SAMPLES - 1):
        token_counter.record_prompt_token_usage(100, 400)
    assert token_counter.get_prompt_estimate_safety_margin() == 128

    gap = token_counter.record_prompt_token_usage(100, 400)

    assert gap == 300
    assert token_counter.get_prompt_estimate_safety_margin() == 364


def test_tokenizer_uses_local_cache_before_network(monkeypatch):
    tokenizer = MagicMock(chat_template="<chat template>")
    loader = MagicMock(side_effect=[OSError("cache miss"), tokenizer])
    monkeypatch.setattr(token_counter, "HF_HUB_OFFLINE", False)
    monkeypatch.setattr(token_counter.AutoTokenizer, "from_pretrained", loader)

    counter = token_counter.TokenCounter("google/gemma-it")

    assert counter.tokenizer is tokenizer
    assert loader.call_count == 2
    assert loader.call_args_list[0].kwargs["local_files_only"] is True
    assert loader.call_args_list[1].kwargs["local_files_only"] is False


def test_tokenizer_stays_local_in_offline_mode(monkeypatch):
    loader = MagicMock(side_effect=OSError("tokenizer is not cached"))
    monkeypatch.setattr(token_counter, "HF_HUB_OFFLINE", True)
    monkeypatch.setattr(token_counter.AutoTokenizer, "from_pretrained", loader)

    with pytest.raises(OSError, match="not cached"):
        token_counter.TokenCounter("google/gemma-it")

    loader.assert_called_once()
    assert loader.call_args.kwargs["local_files_only"] is True


@pytest.mark.asyncio
async def test_token_counter_uses_character_estimate_after_tokenizer_download_fails(
    monkeypatch, caplog
):
    model_name = "test/model-without-tokenizer"
    monkeypatch.setattr(
        token_counter, "_resolve_tokenizer_model", AsyncMock(return_value=model_name)
    )
    monkeypatch.setattr(
        token_counter,
        "_get_tokenizer",
        MagicMock(side_effect=OSError("download failed")),
    )
    monkeypatch.setattr(token_counter, "_TOKENIZER_LOAD_ERRORS", set())
    monkeypatch.setattr(token_counter, "_TOKEN_CACHE", token_counter.OrderedDict())
    monkeypatch.setattr(token_counter, "_INFLIGHT_TOKEN_REQUESTS", {})
    text = "tokenizer download failure fallback check"

    with caplog.at_level("WARNING", logger="token_counter"):
        result = await token_counter.count_token(text)

    assert result == len(text) // 4
    assert model_name in token_counter._TOKENIZER_LOAD_ERRORS
    assert "Token counter fallback selected" in caplog.text


@pytest.mark.asyncio
async def test_token_lru_cache_and_single_flight():
    # 1. Empty string count
    c_empty = await count_token("")
    assert c_empty == 0

    # 2. Count sample text
    text_a = "KSM AIoT Universitas Pembangunan Nasional Veteran Jakarta"
    c_a1 = await count_token(text_a)
    assert c_a1 > 0

    # 3. Cache hit returns same value
    c_a2 = await count_token(text_a)
    assert c_a1 == c_a2

    # 4. Concurrent single-flight deduplication
    text_b = "Testing concurrent single flight tokenize deduplication with Nexo Bot"
    results = await asyncio.gather(
        count_token(text_b),
        count_token(text_b),
        count_token(text_b),
    )
    assert results[0] == results[1] == results[2]
    assert results[0] > 0


@requires_postgres
@pytest.mark.asyncio
async def test_token_analytics_sql_aggregation():
    test_user_1 = 888111222333
    test_user_2 = 888111222444
    guild_id = 999888777666

    # Cleanup previous test records
    async with async_session() as session:
        await session.execute(
            text(
                "DELETE FROM token_usage_logs WHERE user_id IN (:u1, :u2) OR guild_id = :gid"
            ),
            {"u1": test_user_1, "u2": test_user_2, "gid": guild_id},
        )
        await session.commit()

    try:
        # Insert test records
        await log_token_usage(
            guild_id, test_user_1, "TesterAlpha", 1200, 250, 1450, 1500
        )
        await log_token_usage(
            guild_id, test_user_1, "TesterAlpha", 1500, 300, 1800, 1700
        )
        await log_token_usage(
            guild_id, test_user_2, "TesterBeta", 2000, 400, 2400, 2100
        )

        # Aggregate user stats
        stats = await get_user_token_stats(test_user_1)
        assert stats["total_prompt_tokens"] == 2700
        assert stats["total_completion_tokens"] == 550
        assert stats["total_tokens"] == 3250
        assert stats["interactions"] == 2
        assert stats["avg_tokens_per_interaction"] == 1625.0

        # Leaderboard aggregation
        leaderboard, summary = await get_guild_token_leaderboard(
            guild_id=guild_id, limit=5
        )
        assert summary["guild_total_tokens"] == 5650
        assert summary["guild_interactions"] == 3
        assert len(leaderboard) == 2
        assert leaderboard[0]["user_id"] == test_user_1
        assert leaderboard[1]["user_id"] == test_user_2

    finally:
        # Cleanup
        async with async_session() as session:
            await session.execute(
                text(
                    "DELETE FROM token_usage_logs WHERE user_id IN (:u1, :u2) OR guild_id = :gid"
                ),
                {"u1": test_user_1, "u2": test_user_2, "gid": guild_id},
            )
            await session.commit()
