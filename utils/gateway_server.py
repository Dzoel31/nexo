import os
import json
import logging
from pathlib import Path
from typing import Any
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from jinja2 import Environment, FileSystemLoader, select_autoescape
from discord.ext import commands

from utils.verify import verify_signature
from utils.webhook_schemas import (
    PushSchema,
    PullRequestSchema,
    ReleaseSchema,
    WorkflowSchema,
)

logger = logging.getLogger("gateway_server")
app = FastAPI(title="Nexo Webhook Gateway", docs_url="/docs")

# Global reference to discord bot
_bot: commands.Bot | None = None

# Jinja2 Template Loader
TEMPLATES_DIR = Path("templates")
PROJECTS_CONFIG_PATH = Path("config/projects.json")

if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
env_template = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["j2", "html", "xml"]),
)


def load_projects_config() -> dict[str, Any]:
    if PROJECTS_CONFIG_PATH.exists():
        try:
            with open(PROJECTS_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load projects.json: {e}")
    return {}


def should_send_event(event_name: str, model: Any) -> bool:
    if event_name == "pull_request":
        allowed_actions = {
            "opened",
            "reopened",
            "closed",
            "edited",
            "synchronize",
            "ready_for_review",
            "converted_to_draft",
        }
        return getattr(model, "action", None) in allowed_actions
    if event_name == "release":
        return getattr(model, "action", None) in {
            "published",
            "released",
            "prereleased",
        }
    if event_name == "workflow_run":
        wf_run = getattr(model, "workflow_run", None)
        return (
            getattr(model, "action", None) == "completed"
            and wf_run is not None
            and getattr(wf_run, "conclusion", None) is not None
        )
    if event_name == "push":
        return bool(
            getattr(model, "commits", None) or getattr(model, "head_commit", None)
        )
    return True


@app.get("/nexo/health")
async def health_check():
    bot_online = _bot is not None and _bot.is_ready()
    return {
        "status": "healthy",
        "bot_online": bot_online,
        "bot_name": str(_bot.user) if _bot and _bot.user else "Connecting...",
    }


@app.post("/nexo/webhook")
async def webhook_handler(request: Request):
    event = request.headers.get("X-GitHub-Event", "unknown")
    delivery = request.headers.get("X-GitHub-Delivery", "unknown")
    secret = request.headers.get("X-Hub-Signature-256", "")

    raw_body = await request.body()
    verify_signature(raw_body, secret)

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON payload received | event={event} delivery={delivery}"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    logger.info(f"Received GitHub event: '{event}', delivery ID: {delivery}")

    schema_map = {
        "push": PushSchema,
        "pull_request": PullRequestSchema,
        "release": ReleaseSchema,
        "workflow_run": WorkflowSchema,
    }

    cog = _bot.get_cog("WebhookDeployCog") if _bot else None

    schema_cls = schema_map.get(event)
    if schema_cls is None:
        logger.warning(f"Unsupported event type: {event} | delivery={delivery}")
        data_dir = Path("data")
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)

        safe_event_name = (
            "".join(c for c in event if c.isalnum() or c in ("_", "-")) or "unsupported"
        )
        event_file = data_dir / f"{safe_event_name}.json"
        existing = []
        if event_file.exists():
            try:
                with open(event_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = [existing]
            except Exception:
                existing = []

        existing.append(payload)
        with open(event_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=4)

        if cog:
            devlog_msg = {
                "content": (
                    f"⚠️ Received unsupported GitHub event: **{event}**\n"
                    f"Delivery ID: `{delivery}`\n"
                    f"Stored payload to `{event_file}`."
                ),
            }
            asyncio.create_task(cog.send_discord_notification(devlog_msg))

        return {"status": "unsupported_event_stored", "event": event}

    projects_config = load_projects_config()

    if not isinstance(payload, list):
        payload_items = [payload]
    else:
        payload_items = payload

    for item in payload_items:
        try:
            model = schema_cls(**item)
        except Exception as e:
            logger.error(f"Failed to validate payload for event '{event}': {e}")
            raise HTTPException(status_code=500, detail="Payload validation failed.")

        if not should_send_event(event, model):
            logger.info(
                f"Filtered event '{event}' with action '{getattr(model, 'action', None)}'"
            )
            continue

        repo_name = getattr(getattr(model, "repository", None), "name", "")
        repo_full_name = getattr(getattr(model, "repository", None), "full_name", "")
        repo_config = projects_config.get(
            repo_full_name,
            projects_config.get(
                repo_name,
                {
                    "title": "Deployment / Pipeline Event",
                    "emoji": "🚀",
                    "discord_channel_id": None,
                    "discord_role_id": None,
                },
            ),
        )

        template_name = f"{event}_message.j2"
        is_cd_success = False
        if event == "workflow_run" and getattr(model, "action", None) == "completed":
            wf_run = getattr(model, "workflow_run", None)
            if wf_run and getattr(wf_run, "conclusion", None) == "success":
                is_cd_success = True
        elif event == "release" and getattr(model, "action", None) == "published":
            is_cd_success = True

        if is_cd_success:
            template_name = "cd_success_message.j2"

        try:
            template = env_template.get_template(template_name)
        except Exception as e:
            logger.error(f"Template '{template_name}' not found: {e}")
            raise HTTPException(
                status_code=500, detail=f"Template {template_name} not found."
            )

        try:
            rendered_content = template.render(data=model, config=repo_config)
            message_payload = json.loads(rendered_content)
        except Exception as e:
            logger.error(f"Template rendering failed for '{template_name}': {e}")
            raise HTTPException(status_code=500, detail="Template rendering failed.")

        if cog:
            target_channel_id = repo_config.get("discord_channel_id")
            asyncio.create_task(
                cog.send_discord_notification(
                    message_payload, target_channel_id=target_channel_id
                )
            )

            # Global #release-notes Broadcast if CD Success
            if is_cd_success:
                release_notes_channel_id = int(
                    os.environ.get("WEBHOOK_RELEASE_NOTES_CHANNEL_ID", 0) or 0
                )
                if (
                    release_notes_channel_id
                    and release_notes_channel_id != target_channel_id
                ):
                    asyncio.create_task(
                        cog.send_discord_notification(
                            message_payload, target_channel_id=release_notes_channel_id
                        )
                    )

            # Auto-Deploy Trigger Check
            repo_key = repo_name or repo_full_name
            if is_cd_success and event == "workflow_run":
                asyncio.create_task(
                    cog.trigger_docker_compose(
                        repo_key=repo_key,
                        repo_name=repo_full_name,
                        target_channel_id=target_channel_id,
                    )
                )

    return {"status": "success", "event": event, "delivery": delivery}


async def start_gateway_server(bot: commands.Bot):
    global _bot
    _bot = bot

    host = os.environ.get("HOST", "0.0.0.0")  # nosec B104
    port = int(os.environ.get("PORT", os.environ.get("WEBHOOK_PORT", 8000)))
    config = uvicorn.Config(
        app=app, host=host, port=port, log_level="info", access_log=False
    )
    server = uvicorn.Server(config)
    logger.info(f"Starting FastAPI Webhook Gateway Server on port {port}...")
    await server.serve()
