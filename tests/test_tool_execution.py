import asyncio

import pytest

from utils.mcp_client import _execute_tool_calls, sanitize_tools_list
from utils.schemas import DiscordEventSchema


def test_discord_event_schema_time_cleaning():
    payload = {
        "name": "Meeting Evaluasi",
        "description": "Evaluasi progres proyek bulanan.",
        "start_date": "2026-09-02",
        "start_time": "13:00",
        "location": "Voice Channel: Umum",
        "target_role": "@everyone",
    }
    event = DiscordEventSchema.model_validate(payload)
    assert event.name == "Meeting Evaluasi"
    assert event.start_time == "13:00:00"
    assert event.target_role == "@everyone"


def test_sanitize_tools_list():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A dummy tool description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "title": "Param 1"},
                    },
                    "required": ["param1"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    sanitized = sanitize_tools_list(tools)
    assert len(sanitized) == 1
    func = sanitized[0]["function"]
    assert func["name"] == "test_tool"
    # Title and additionalProperties should be cleaned
    props = func["parameters"]["properties"]["param1"]
    assert "title" not in props


@pytest.mark.asyncio
async def test_read_only_tool_calls_run_concurrently_and_keep_result_order():
    both_started = asyncio.Event()
    started = set()

    async def lookup(arguments):
        started.add(arguments["name"])
        if len(started) == 2:
            both_started.set()
        await asyncio.wait_for(both_started.wait(), timeout=1)
        return arguments["name"]

    bot = type("Bot", (), {"local_tool_handlers": {"lookup": lookup}})()
    calls = [
        {"tool_name": "lookup", "arguments": {"name": "first"}, "error": None},
        {"tool_name": "lookup", "arguments": {"name": "second"}, "error": None},
    ]

    results = await _execute_tool_calls(bot, calls, {"lookup"}, None)

    assert results == ["first", "second"]


@pytest.mark.asyncio
async def test_mutating_tool_calls_remain_sequential():
    execution_order = []

    async def mutate(arguments):
        execution_order.append(f"start:{arguments['name']}")
        await asyncio.sleep(0)
        execution_order.append(f"done:{arguments['name']}")
        return arguments["name"]

    bot = type("Bot", (), {"local_tool_handlers": {"mutate": mutate}})()
    calls = [
        {"tool_name": "mutate", "arguments": {"name": "first"}, "error": None},
        {"tool_name": "mutate", "arguments": {"name": "second"}, "error": None},
    ]

    results = await _execute_tool_calls(bot, calls, set(), None)

    assert results == ["first", "second"]
    assert execution_order == [
        "start:first",
        "done:first",
        "start:second",
        "done:second",
    ]
