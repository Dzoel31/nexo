"""Token counting with remote counting and a bounded single-flight cache."""

import asyncio
import hashlib
from collections import OrderedDict

from openai import AsyncOpenAI

from config.settings import settings

LLM_BASE_URL = settings.LLM_BASE_URL
LLM_API_KEY = settings.LLM_API_KEY.strip("\"' \r\n")
TOTAL_CONTEXT_WINDOW = settings.TOTAL_CONTEXT_WINDOW
MAX_COMPLETION_TOKENS = 1024
BASE_OVERHEAD_TOKENS = 1400
TOOL_BUFFER_TOKENS = 1200
LLM_MODEL_NAME = settings.LLM_MODEL_NAME
USABLE_HISTORY_BUDGET = max(
    1000,
    TOTAL_CONTEXT_WINDOW
    - (MAX_COMPLETION_TOKENS + BASE_OVERHEAD_TOKENS + TOOL_BUFFER_TOKENS),
)
COMPACTION_THRESHOLD = int(USABLE_HISTORY_BUDGET)
TARGET_RETAIN_TOKENS = int(USABLE_HISTORY_BUDGET * 0.40)

_TOKEN_CACHE: OrderedDict[str, int] = OrderedDict()
_MAX_CACHE_SIZE = 1000
_INFLIGHT_TOKEN_REQUESTS: dict[str, asyncio.Future[int]] = {}

ai_client = AsyncOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY or "sk-no-key",
)


async def count_token(text_content: str) -> int:
    """Count tokens remotely, with LRU caching and a local fallback estimate."""
    if not text_content:
        return 0

    text_hash = hashlib.md5(
        text_content.encode("utf-8"), usedforsecurity=False
    ).hexdigest()
    if text_hash in _TOKEN_CACHE:
        _TOKEN_CACHE.move_to_end(text_hash)
        return _TOKEN_CACHE[text_hash]
    if text_hash in _INFLIGHT_TOKEN_REQUESTS:
        return await _INFLIGHT_TOKEN_REQUESTS[text_hash]

    loop = asyncio.get_running_loop()
    future: asyncio.Future[int] = loop.create_future()
    _INFLIGHT_TOKEN_REQUESTS[text_hash] = future
    token_count = 0
    try:
        response = await ai_client.responses.input_tokens.count(
            model=LLM_MODEL_NAME,
            input=text_content,
        )
        token_count = int(response.input_tokens)
    except Exception:  # noqa: BLE001
        token_count = max(1, len(text_content) // 4)
    finally:
        if not future.done():
            future.set_result(token_count)
        _INFLIGHT_TOKEN_REQUESTS.pop(text_hash, None)

    if len(_TOKEN_CACHE) >= _MAX_CACHE_SIZE:
        _TOKEN_CACHE.popitem(last=False)
    _TOKEN_CACHE[text_hash] = token_count
    return token_count
