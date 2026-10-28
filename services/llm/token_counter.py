"""Token counting with remote counting and a bounded single-flight cache."""

import asyncio
import hashlib
from collections import OrderedDict

import aiohttp
from openai import AsyncOpenAI

from config.settings import settings

LLM_BASE_URL = settings.LLM_BASE_URL
LLM_API_KEY = settings.LLM_API_KEY.strip("\"' \r\n")
LLM_TOKENIZE_URL = settings.LLM_TOKENIZE_URL.strip()
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
    """Count tokens using an optional provider-specific endpoint or an estimate."""
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
        if LLM_TOKENIZE_URL:
            headers = {}
            if LLM_API_KEY and LLM_API_KEY != "sk-no-key":
                headers["Authorization"] = f"Bearer {LLM_API_KEY}"
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    LLM_TOKENIZE_URL,
                    json={"content": text_content},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response,
            ):
                response.raise_for_status()
                payload = await response.json()
                tokens = payload.get("tokens")
                if isinstance(tokens, list):
                    token_count = len(tokens)
                else:
                    token_count = int(payload["count"])
        else:
            token_count = max(1, len(text_content) // 4)
    except aiohttp.ClientError, KeyError, TypeError, ValueError:
        token_count = max(1, len(text_content) // 4)
    finally:
        if not future.done():
            future.set_result(token_count)
        _INFLIGHT_TOKEN_REQUESTS.pop(text_hash, None)

    if len(_TOKEN_CACHE) >= _MAX_CACHE_SIZE:
        _TOKEN_CACHE.popitem(last=False)
    _TOKEN_CACHE[text_hash] = token_count
    return token_count
