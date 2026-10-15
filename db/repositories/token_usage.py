import logging
from datetime import UTC, datetime

from sqlalchemy import text

from db.session import async_session

logger = logging.getLogger("chat_repository")


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
        now_utc = datetime.now(UTC)
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
    except Exception as e:  # noqa: BLE001
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
