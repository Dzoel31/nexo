import asyncio
import pytest
from sqlalchemy import text
from db.repository import (
    count_token,
    get_guild_token_leaderboard,
    get_user_token_stats,
    log_token_usage,
)
from db.session import async_session


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
