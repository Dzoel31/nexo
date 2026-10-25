import asyncio
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import discord

DELETE_DELAY_SECONDS = 1.5
MAX_BULK_DELETE_AGE = timedelta(days=14)
MAX_BULK_DELETE_COUNT = 100


async def slow_purge(
    channel: Any,
    *,
    limit: int,
    check: Callable[[discord.Message], bool] | None = None,
    reason: str | None = None,
) -> list[discord.Message]:
    """Delete messages with a controlled request rate to avoid Discord 429 responses."""
    messages = [
        message
        async for message in channel.history(limit=limit)
        if check is None or check(message)
    ]
    if not messages:
        return []

    now = discord.utils.utcnow()
    deleted: list[discord.Message] = []
    last_request_at = 0.0

    async def wait_between_requests() -> None:
        nonlocal last_request_at
        loop = asyncio.get_running_loop()
        elapsed = loop.time() - last_request_at
        if last_request_at and elapsed < DELETE_DELAY_SECONDS:
            await asyncio.sleep(DELETE_DELAY_SECONDS - elapsed)
        last_request_at = loop.time()

    recent_messages: list[discord.Message] = []
    for message in messages:
        if now - message.created_at < MAX_BULK_DELETE_AGE:
            recent_messages.append(message)
            continue

        if recent_messages:
            await _bulk_delete(
                channel,
                recent_messages,
                reason=reason,
                wait_between_requests=wait_between_requests,
                deleted=deleted,
            )
            recent_messages = []

        await wait_between_requests()
        await message.delete(reason=reason)
        deleted.append(message)

    if recent_messages:
        await _bulk_delete(
            channel,
            recent_messages,
            reason=reason,
            wait_between_requests=wait_between_requests,
            deleted=deleted,
        )

    return deleted


async def _bulk_delete(
    channel: Any,
    messages: list[discord.Message],
    *,
    reason: str | None,
    wait_between_requests: Callable[[], Any],
    deleted: list[discord.Message],
) -> None:
    for start in range(0, len(messages), MAX_BULK_DELETE_COUNT):
        batch = messages[start : start + MAX_BULK_DELETE_COUNT]
        await wait_between_requests()
        await channel.delete_messages(batch, reason=reason)
        deleted.extend(batch)
