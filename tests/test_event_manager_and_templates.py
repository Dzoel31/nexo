from datetime import datetime, timedelta, timezone
from utils.event_manager import (
    format_indonesian_date,
    format_time_wib,
    get_human_time_label,
    prune_reminder_intervals,
    to_wib,
)
from utils.template_renderer import render_event_template


def test_timezone_wib_conversion():
    # 06:00 UTC must be converted to 13:00 WIB
    dt_utc = datetime(2026, 9, 1, 6, 0, tzinfo=timezone.utc)
    assert format_time_wib(dt_utc) == "13:00"
    assert "Selasa, 01 September 2026" in format_indonesian_date(dt_utc)

    # 13:00 WIB directly
    wib_tz = timezone(timedelta(hours=7))
    dt_wib = datetime(2026, 9, 1, 13, 0, tzinfo=wib_tz)
    assert format_time_wib(dt_wib) == "13:00"
    assert to_wib(dt_utc) == dt_wib


def test_reminder_interval_pruning():
    now = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    # Event starting in 45 minutes
    start = now + timedelta(minutes=45)

    valid_intervals = prune_reminder_intervals(start_time=start, now_dt=now)
    # Rule: trigger_time > now + 5 min.
    # 45 - 30 = 15 > 5 -> included (30)
    # 45 - 10 = 35 > 5 -> included (10)
    # 45 - 60 = -15 < 5 -> pruned (60)
    assert 30 in valid_intervals
    assert 10 in valid_intervals
    assert 60 not in valid_intervals
    assert 1440 not in valid_intervals


def test_human_time_labels():
    assert get_human_time_label(10080) == "H-7 Hari"
    assert get_human_time_label(1440) == "H-1 Hari"
    assert get_human_time_label(60) == "1 Jam Lagi"
    assert get_human_time_label(10) == "10 Menit Lagi"


def test_template_rendering():
    event_mock = {
        "name": "Workshop Edge AI",
        "description": "Agenda pembelajaran YOLOv8 & Coral TPU.",
        "location": "Voice Channel: Meeting 1",
        "event_url": "https://discord.com/events/123456789/987654321",
    }
    dt = datetime(2026, 9, 2, 13, 0, tzinfo=timezone(timedelta(hours=7)))

    ctx_initial = {
        "event": event_mock,
        "formatted_date": format_indonesian_date(dt),
        "formatted_time": format_time_wib(dt),
        "role_mention": "<@&1465662834540023920>",
    }
    rendered_initial = render_event_template("events/broadcast_initial.j2", ctx_initial)
    assert "PENGUMUMAN ACARA BARU" in rendered_initial
    assert "Workshop Edge AI" in rendered_initial
    assert "13:00 WIB" in rendered_initial
    assert "<@&1465662834540023920>" in rendered_initial

    ctx_reminder = {
        "event": event_mock,
        "time_label": "30 Menit Lagi",
        "formatted_time": format_time_wib(dt),
        "role_mention": "@everyone",
    }
    rendered_reminder = render_event_template(
        "events/default_reminder.j2", ctx_reminder
    )
    assert "PENGINGAT ACARA: 30 Menit Lagi!" in rendered_reminder
    assert "@everyone" in rendered_reminder


def test_webhook_release_template_json_rendering():
    import json
    from jinja2 import Environment, FileSystemLoader
    from utils.webhook_schemas import ReleaseSchema

    from utils.gateway_server import compact_markdown

    env = Environment(loader=FileSystemLoader("templates"), autoescape=False)
    env.filters["compact_markdown"] = compact_markdown
    template = env.get_template("release_message.j2")

    user_mock = {
        "login": "github-actions[bot]",
        "id": 12345,
        "avatar_url": "https://avatars.githubusercontent.com/in/15368?v=4",
        "html_url": "https://github.com/apps/github-actions",
    }
    sample_release = {
        "action": "released",
        "release": {
            "url": "https://api.github.com/repos/ksm-aiot-upnvj/nexo/releases/123",
            "html_url": "https://github.com/ksm-aiot-upnvj/nexo/releases/tag/1.9.0",
            "id": 123456,
            "author": user_mock,
            "tag_name": "1.9.0",
            "name": "1.9.0",
            "draft": False,
            "prerelease": False,
            "created_at": "2026-09-01T06:45:00Z",
            "updated_at": "2026-09-01T06:45:00Z",
            "published_at": "2026-09-01T06:45:00Z",
            "body": "## 1.9.0 (2026-09-01)\n\n* **feat:** quote \"test\" & \\backslashes\\ and code:\n```python\nprint('hello')\n```",
        },
        "repository": {
            "name": "nexo",
            "full_name": "ksm-aiot-upnvj/nexo",
            "private": False,
            "html_url": "https://github.com/ksm-aiot-upnvj/nexo",
            "owner": user_mock,
        },
        "sender": user_mock,
    }
    model = ReleaseSchema(**sample_release)
    config = {"discord_channel_id": 123456, "discord_role_id": None}

    rendered = template.render(data=model, config=config)
    parsed = json.loads(rendered)
    assert "content" in parsed
    assert "embeds" in parsed
    assert len(parsed["embeds"]) == 1
    assert (
        "1.9.0" in parsed["embeds"][0]["title"]
        or "nexo" in parsed["embeds"][0]["title"]
    )
