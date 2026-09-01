from utils.mcp_client import sanitize_tools_list
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
