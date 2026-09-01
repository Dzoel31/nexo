import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from utils.webhook_schemas import (
    PushSchema,
    PullRequestSchema,
    ReleaseSchema,
    WorkflowSchema,
)

from utils.gateway_server import compact_markdown

env = Environment(loader=FileSystemLoader("templates"), autoescape=False)
env.filters["compact_markdown"] = compact_markdown
dummy_config = {
    "title": "Service Deploy",
    "emoji": "🚀",
    "discord_channel_id": 123456,
    "discord_role_id": 987654,
}


def test_actual_release_payload_rendering():
    payload_path = Path("release_payload.json")
    if not payload_path.exists():
        return

    with open(payload_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    model = ReleaseSchema(**data)
    template = env.get_template("release_message.j2")
    rendered = template.render(data=model, config=dummy_config)
    parsed = json.loads(rendered)

    assert "content" in parsed
    assert "embeds" in parsed
    assert len(parsed["embeds"]) == 1
    assert "1.10.0" in parsed["content"]
    assert "1.10.0" in parsed["embeds"][0]["description"]
    assert parsed["embeds"][0]["color"] == 3066993


def test_push_template_rendering_with_special_characters():
    user = {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
    }
    repo = {
        "name": "test-repo",
        "full_name": "org/test-repo",
        "private": False,
        "html_url": "https://github.com/org/test-repo",
        "owner": user,
    }
    commit = {
        "id": "1234567890abcdef",
        "message": 'fix: handle "quoted text" & \\backslashes\\ and \n newlines',
        "url": "https://github.com/org/test-repo/commit/1234567890abcdef",
        "author": {"name": "Dev", "email": "dev@example.com"},
        "committer": {"name": "Dev", "email": "dev@example.com"},
        "timestamp": "2026-09-01T12:00:00Z",
    }
    payload = {
        "ref": "refs/heads/main",
        "before": "000000",
        "after": "123456",
        "repository": repo,
        "pusher": {"name": "octocat", "email": "octocat@github.com"},
        "sender": user,
        "created": False,
        "deleted": False,
        "forced": False,
        "compare": "https://github.com/org/test-repo/compare/0000...1234",
        "commits": [commit],
        "head_commit": commit,
    }

    model = PushSchema(**payload)
    template = env.get_template("push_message.j2")
    rendered = template.render(data=model, config=dummy_config)
    parsed = json.loads(rendered)

    assert "content" in parsed
    assert "embeds" in parsed
    assert len(parsed["embeds"]) == 1


def test_pull_request_template_rendering():
    user = {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
    }
    repo = {
        "name": "test-repo",
        "full_name": "org/test-repo",
        "private": False,
        "html_url": "https://github.com/org/test-repo",
        "owner": user,
    }
    pr = {
        "url": "https://api.github.com/repos/org/test-repo/pulls/1",
        "id": 100,
        "html_url": "https://github.com/org/test-repo/pull/1",
        "number": 1,
        "state": "open",
        "title": 'feat: "awesome new feature" with \\escape\\',
        "user": user,
        "body": "PR description with markdown\n- list item",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
        "head": {"ref": "feature-branch", "sha": "abc1234"},
        "base": {"ref": "main", "sha": "def5678"},
        "draft": False,
    }
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": pr,
        "repository": repo,
        "sender": user,
    }

    model = PullRequestSchema(**payload)
    template = env.get_template("pull_request_message.j2")
    rendered = template.render(data=model, config=dummy_config)
    parsed = json.loads(rendered)

    assert "content" in parsed
    assert "embeds" in parsed


def test_workflow_run_template_rendering():
    user = {
        "login": "octocat",
        "id": 1,
        "avatar_url": "https://github.com/images/error/octocat_happy.gif",
        "html_url": "https://github.com/octocat",
    }
    repo = {
        "name": "test-repo",
        "full_name": "org/test-repo",
        "private": False,
        "html_url": "https://github.com/org/test-repo",
        "owner": user,
    }
    wf = {
        "id": 555,
        "name": "Build & Push Docker",
        "head_branch": "main",
        "head_sha": "999888777",
        "path": ".github/workflows/deploy.yml",
        "display_title": 'build: "release container" \\v1.0\\',
        "run_number": 42,
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "html_url": "https://github.com/org/test-repo/actions/runs/555",
        "created_at": "2026-09-01T11:00:00Z",
        "updated_at": "2026-09-01T11:05:00Z",
        "triggering_actor": user,
    }
    payload = {
        "action": "completed",
        "workflow_run": wf,
        "repository": repo,
        "sender": user,
    }

    model = WorkflowSchema(**payload)
    template = env.get_template("workflow_run_message.j2")
    rendered = template.render(data=model, config=dummy_config)
    parsed = json.loads(rendered)

    assert "content" in parsed
    assert "embeds" in parsed
