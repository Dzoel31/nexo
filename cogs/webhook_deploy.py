import os
import json
import logging
import asyncio
import subprocess  # nosec B404
from pathlib import Path
from typing import Any, List, Union
import aiohttp
import discord
from discord.ext import commands
from utils.webhook_schemas import DockerServiceSchema

logger = logging.getLogger("cogs.webhook_deploy")


def resolve_path(value: str) -> Path | None:
    if not value:
        return None
    return Path(value).expanduser()


def parse_compose_paths(raw_paths: str) -> dict[str, Path]:
    compose_paths: dict[str, Path] = {}
    if not raw_paths:
        return compose_paths

    raw_paths = raw_paths.strip()
    if not raw_paths:
        return compose_paths

    if raw_paths.startswith("{"):
        try:
            parsed = json.loads(raw_paths)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    res = resolve_path(str(v))
                    if res:
                        compose_paths[str(k)] = res
        except json.JSONDecodeError:
            logger.warning("Failed to parse DOCKER_COMPOSE_PATHS as JSON")
        return compose_paths

    for entry in raw_paths.split(";"):
        entry = entry.strip()
        if not entry or "=" not in entry:
            continue
        repo_key, path_val = entry.split("=", 1)
        repo_key = repo_key.strip()
        path_val = path_val.strip()
        if repo_key and path_val:
            res = resolve_path(path_val)
            if res:
                compose_paths[repo_key] = res

    return compose_paths


def build_project_paths() -> dict[str, Path]:
    raw = os.environ.get("DOCKER_COMPOSE_PATHS", "")
    paths = parse_compose_paths(raw)

    backend = resolve_path(os.environ.get("PATH_BACKEND_HYDROPONIC", ""))
    if backend:
        paths.setdefault("smart-hydroponic-backend", backend)

    projects_config_path = Path("config/projects.json")
    if projects_config_path.exists():
        try:
            with open(projects_config_path, "r", encoding="utf-8") as f:
                projects_data = json.load(f)
                if isinstance(projects_data, dict):
                    for repo_key, cfg in projects_data.items():
                        if isinstance(cfg, dict) and cfg.get("deploy_path"):
                            res = resolve_path(str(cfg["deploy_path"]))
                            if res:
                                paths.setdefault(repo_key, res)
                                # Also set for short name if full_name is repo_key
                                short_name = repo_key.split("/")[-1]
                                paths.setdefault(short_name, res)
        except Exception as err:
            logger.warning(
                f"Could not read deploy_path from config/projects.json: {err}"
            )

    return paths


def truncate_output(text: str, limit: int = 1800) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 50] + "\n... (truncated) ..."


class WebhookDeployCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.project_paths = build_project_paths()

    async def send_discord_notification(
        self, payload: dict[str, Any], target_channel_id: int | None = None
    ):
        """Send notification via webhook URL or bot text channel."""
        if target_channel_id:
            channel = self.bot.get_channel(target_channel_id)
            if channel:
                content = payload.get("content", "")
                embeds_data = payload.get("embeds", [])
                discord_embeds = []

                for emb in embeds_data:
                    try:
                        embed = discord.Embed.from_dict(emb)
                        discord_embeds.append(embed)
                    except Exception as e:
                        logger.error(f"Failed to parse embed dict: {e}")

                await channel.send(content=content, embeds=discord_embeds)
                return
            else:
                logger.warning(
                    f"Target channel ID {target_channel_id} not found in bot, fallback to default."
                )

        webhook_url = os.environ.get("WEBHOOK_DEVLOGS_CHANNEL", "")
        if webhook_url.startswith("http://") or webhook_url.startswith("https://"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url, json=payload, timeout=10
                    ) as resp:
                        if resp.status not in (200, 204):
                            logger.warning(
                                f"Webhook URL returned non-200 status: {resp.status}"
                            )
            except Exception as e:
                logger.error(f"Failed to post to Webhook URL: {e}")
            return

        # Fallback to Channel ID
        channel_id = int(os.environ.get("WEBHOOK_DEVLOGS_CHANNEL_ID", 0) or 0)
        if not channel_id and webhook_url.isdigit():
            channel_id = int(webhook_url)

        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                content = payload.get("content", "")
                embeds_data = payload.get("embeds", [])
                discord_embeds = []

                for emb in embeds_data:
                    try:
                        embed = discord.Embed.from_dict(emb)
                        discord_embeds.append(embed)
                    except Exception as e:
                        logger.error(f"Failed to parse embed dict: {e}")

                await channel.send(content=content, embeds=discord_embeds)
            else:
                logger.warning(f"Could not find Discord channel with ID {channel_id}")
        else:
            logger.warning(
                "No WEBHOOK_DEVLOGS_CHANNEL or WEBHOOK_DEVLOGS_CHANNEL_ID configured."
            )

    async def run_command_async(
        self, cmd: List[str], work_dir: Path
    ) -> tuple[int, str]:
        def _exec():
            # Executed safely with fixed list args and no shell expansion
            exec_cmd = list(cmd)
            actual_cwd = None

            if work_dir and work_dir.exists():
                actual_cwd = str(work_dir)
            elif work_dir:
                # If work_dir is a host VPS path not mounted in container, pass -f docker-compose.yml to docker compose
                compose_file = work_dir / "docker-compose.yml"
                if (
                    len(exec_cmd) >= 2
                    and exec_cmd[0] == "docker"
                    and exec_cmd[1] == "compose"
                ):
                    exec_cmd = [
                        "docker",
                        "compose",
                        "-f",
                        str(compose_file),
                    ] + exec_cmd[2:]
                # Check fallback directory in container (/app)
                if Path("/app").exists():
                    actual_cwd = "/app"

            result = subprocess.run(  # nosec B603
                exec_cmd,
                cwd=actual_cwd,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            combined = "\n".join(
                line for line in [result.stdout.strip(), result.stderr.strip()] if line
            )
            return result.returncode, combined

        return await asyncio.to_thread(_exec)

    async def list_compose_services(self, work_dir: Path) -> List[DockerServiceSchema]:
        code, raw = await self.run_command_async(
            ["docker", "compose", "ps", "--format", "json"], work_dir
        )
        services: List[DockerServiceSchema] = []
        for line in raw.splitlines():
            json_start = line.find("{")
            if json_start == -1:
                continue
            try:
                service_info = json.loads(line[json_start:])
                services.append(DockerServiceSchema(**service_info))
            except (json.JSONDecodeError, ValueError) as err:
                logger.debug(f"Could not parse docker service line: {err}")
        return services

    async def compose_status_summary(
        self, work_dir: Path
    ) -> Union[List[dict[str, Any]], str]:
        max_retries = 12
        interval = 5
        final_status: List[DockerServiceSchema] = []

        for _ in range(max_retries):
            current_services = await self.list_compose_services(work_dir)
            pending = [
                s
                for s in current_services
                if "starting" in s.status.lower() or "unhealthy" in s.status.lower()
            ]
            if not pending and current_services:
                final_status = current_services
                break
            await asyncio.sleep(interval)

        if not final_status:
            final_status = await self.list_compose_services(work_dir)

        if not final_status:
            return "No container statuses reported."

        embeds: List[dict[str, Any]] = []
        for service in final_status:
            embeds.append(
                {
                    "title": f"🐳 Service: {service.name} | ID: {service.id}",
                    "color": service.get_color(),
                    "fields": [
                        {"name": "Status", "value": service.status, "inline": True},
                        {"name": "State", "value": service.state, "inline": True},
                        {"name": "Image", "value": service.image, "inline": False},
                        {
                            "name": "Created",
                            "value": service.createdAt,
                            "inline": False,
                        },
                    ],
                }
            )

        return embeds

    async def trigger_docker_compose(
        self,
        repo_key: str,
        repo_name: str = "",
        target_channel_id: int | None = None,
        announcement_payload: dict[str, Any] | None = None,
    ):
        self.project_paths = build_project_paths()
        work_dir = self.project_paths.get(repo_key)
        if not work_dir:
            logger.warning(
                f"No Docker compose path configured for repo={repo_key}. Skipping deployment."
            )
            return

        target_display = repo_name or repo_key
        is_self_update = "nexo" in target_display.lower()

        logger.info(
            f"Triggering async Docker compose deployment for {target_display} at {work_dir}"
        )

        try:
            # If self-updating Nexo, send a pre-notification first before container restarts
            if is_self_update:
                pre_payload = {
                    "content": (
                        f"🔄 **Self-Update Initiated for {target_display}**\n"
                        f"Menarik image terbaru dan me-recreate kontainer Nexo dalam 5 detik..."
                    ),
                }
                await self.send_discord_notification(
                    pre_payload, target_channel_id=target_channel_id
                )
                await asyncio.sleep(5)

            # 1. Pull
            code_pull, out_pull = await self.run_command_async(
                ["docker", "compose", "pull"], work_dir
            )
            if code_pull != 0:
                raise RuntimeError(f"docker compose pull failed: {out_pull}")

            # 2. Up -d
            code_up, out_up = await self.run_command_async(
                ["docker", "compose", "up", "-d"], work_dir
            )
            if code_up != 0:
                raise RuntimeError(f"docker compose up -d failed: {out_up}")

            # 3. Prune -f
            await self.run_command_async(["docker", "image", "prune", "-f"], work_dir)

            # 4. Status Summary
            status_output = await self.compose_status_summary(work_dir)
            out_up_clean = out_up.strip()

            payload = {
                "content": (
                    f"🧰 Docker Compose Deployment Status for **{target_display}**:\n"
                    f"```bash\n{out_up_clean}\n```"
                ),
            }

            if isinstance(status_output, list):
                payload["embeds"] = status_output
            else:
                payload["content"] += f"\n```\n{status_output}\n```"

            await self.send_discord_notification(
                payload, target_channel_id=target_channel_id
            )
            logger.info(f"Docker compose deployment completed for {target_display}")

            # 5. Send Rich CD Release Announcement after successful VPS Deployment
            if announcement_payload:
                await self.send_discord_notification(
                    announcement_payload, target_channel_id=target_channel_id
                )

                # Broadcast to global #release-notes channel
                release_notes_channel_id = int(
                    os.environ.get("WEBHOOK_RELEASE_NOTES_CHANNEL_ID", 0) or 0
                )
                if (
                    release_notes_channel_id
                    and release_notes_channel_id != target_channel_id
                ):
                    await self.send_discord_notification(
                        announcement_payload,
                        target_channel_id=release_notes_channel_id,
                    )

        except Exception as e:
            err_msg = truncate_output(str(e))
            logger.error(f"Docker compose deployment failed: {err_msg}")
            fail_payload = {
                "content": (
                    f"❌ **Deploy Failed**\n"
                    f"Repo: **{target_display}**\n"
                    f"```\n{err_msg}\n```"
                ),
            }
            await self.send_discord_notification(
                fail_payload, target_channel_id=target_channel_id
            )


async def setup(bot):
    await bot.add_cog(WebhookDeployCog(bot))
