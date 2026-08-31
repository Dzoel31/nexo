import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import re

import discord
from discord.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from db.models import ScheduledEvent
from db.session import async_session
from utils.event_manager import (
    format_indonesian_date,
    format_time_wib,
    get_human_time_label,
    prune_reminder_intervals,
)
from utils.schemas import (
    CheckVoiceChannelSchema,
    ClearMessagesSchema,
    DiscordEventSchema,
    DiscordPollSchema,
    DiscordThreadSchema,
    EndDiscordEventSchema,
    EndDiscordPollSchema,
    GetServerChannelsSchema,
    GetServerRolesSchema,
)
from utils.template_renderer import render_event_template

logger = logging.getLogger("server_events")


class ServerEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder_loop.start()

    def cog_unload(self):
        self.reminder_loop.cancel()

    async def cog_load(self):
        # Initialize properties if they don't exist
        if not hasattr(self.bot, "ai_tools"):
            self.bot.ai_tools = []
        if not hasattr(self.bot, "local_tool_handlers"):
            self.bot.local_tool_handlers = {}

        # Clear old tools from this cog if any (prevents duplication on reload)
        self.bot.ai_tools = [
            t
            for t in self.bot.ai_tools
            if t.get("function", {}).get("name")
            not in [
                "create_discord_event",
                "end_discord_event",
                "create_discord_thread",
                "create_discord_poll",
                "end_discord_poll",
                "get_server_channels",
                "get_server_roles",
                "clear_messages",
                "check_voice_channel",
            ]
        ]

        # 1. Register Pydantic tool schemas to bot memory
        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "create_discord_event",
                    "description": "Schedule a new server event or meeting.",
                    "parameters": DiscordEventSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["create_discord_event"] = self.create_event_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "end_discord_event",
                    "description": "End, close, or stop a Discord Scheduled Event.",
                    "parameters": EndDiscordEventSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["end_discord_event"] = self.end_event_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "create_discord_thread",
                    "description": "Create a new thread in current channel.",
                    "parameters": DiscordThreadSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["create_discord_thread"] = (
            self.create_thread_handler
        )

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "create_discord_poll",
                    "description": "Create an interactive native poll.",
                    "parameters": DiscordPollSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["create_discord_poll"] = self.create_poll_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "end_discord_poll",
                    "description": "End an active poll and get final votes.",
                    "parameters": EndDiscordPollSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["end_discord_poll"] = self.end_poll_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "get_server_channels",
                    "description": "List all server text and voice channels.",
                    "parameters": GetServerChannelsSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["get_server_channels"] = self.get_channels_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "get_server_roles",
                    "description": "List all server roles and IDs.",
                    "parameters": GetServerRolesSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["get_server_roles"] = self.get_roles_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "clear_messages",
                    "description": "Delete messages in bulk.",
                    "parameters": ClearMessagesSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["clear_messages"] = self.clear_messages_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "check_voice_channel",
                    "description": "List users in a voice channel.",
                    "parameters": CheckVoiceChannelSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["check_voice_channel"] = (
            self.check_voice_channel_handler
        )

    async def create_event_handler(self, arguments: dict, ctx_obj=None) -> str:
        """Function called by the LLM brain when create_discord_event tool is used"""
        try:
            # Strict validation using Pydantic
            event_data = DiscordEventSchema.model_validate(arguments)

            # Combine date and time, then add +07:00 (WIB) to make it timezone-aware
            start_str = f"{event_data.start_date}T{event_data.start_time}+07:00"
            start_dt = datetime.fromisoformat(start_str)

            # For end_time, if provided we parse it, otherwise we set a default of +2 hours
            if event_data.end_date and event_data.end_time:
                end_str = f"{event_data.end_date}T{event_data.end_time}+07:00"
                end_dt = datetime.fromisoformat(end_str)
            else:
                end_dt = start_dt + timedelta(hours=2)

            # Get the guild/server object where this bot is located
            if not self.bot.guilds:
                return "❌ Failed: Bot is not currently in any server."
            guild = self.bot.guilds[0]

            # Check if the location matches a Voice Channel or Stage Channel name in the server
            vc = None
            for channel in guild.voice_channels + guild.stage_channels:
                if channel.name.lower() == event_data.location.lower():
                    vc = channel
                    break

            if vc:
                # Create internal event (in a Voice/Stage Channel)
                discord_event = await guild.create_scheduled_event(
                    name=event_data.name,
                    description=event_data.description,
                    start_time=start_dt,
                    end_time=end_dt,
                    channel=vc,
                    entity_type=discord.EntityType.voice
                    if isinstance(vc, discord.VoiceChannel)
                    else discord.EntityType.stage_instance,
                    privacy_level=discord.PrivacyLevel.guild_only,
                )
                loc_str = vc.name
            else:
                # Create external event (Somewhere Else)
                discord_event = await guild.create_scheduled_event(
                    name=event_data.name,
                    description=event_data.description,
                    start_time=start_dt,
                    end_time=end_dt,
                    entity_type=discord.EntityType.external,
                    location=event_data.location,
                    privacy_level=discord.PrivacyLevel.guild_only,
                )
                loc_str = event_data.location

            event_url = f"https://discord.com/events/{guild.id}/{discord_event.id}"

            # Determine Announcement / Broadcast Channel
            announcement_channel_id = int(
                os.environ.get("ANNOUNCEMENT_CHANNEL_ID", "0")
            )
            broadcast_channel = None
            if announcement_channel_id:
                broadcast_channel = self.bot.get_channel(announcement_channel_id)
                if not broadcast_channel:
                    try:
                        broadcast_channel = await self.bot.fetch_channel(
                            announcement_channel_id
                        )
                    except Exception:
                        broadcast_channel = None

            if not broadcast_channel:
                broadcast_channel = getattr(ctx_obj, "channel", guild.system_channel)

            # Render Broadcast Template via Jinja2
            initial_context = {
                "event": {
                    "name": event_data.name,
                    "description": event_data.description or "",
                    "location": loc_str,
                    "event_url": event_url,
                },
                "formatted_date": format_indonesian_date(start_dt),
                "formatted_time": format_time_wib(start_dt),
                "role_mention": None,
            }

            broadcast_msg = None
            if broadcast_channel:
                try:
                    rendered_msg = render_event_template(
                        "events/broadcast_initial.j2", initial_context
                    )
                    broadcast_msg = await broadcast_channel.send(rendered_msg)
                except Exception as b_err:
                    logger.error(f"Failed to send initial event broadcast: {b_err}")

            # Prune reminder intervals based on lead time
            pruned_intervals = prune_reminder_intervals(start_dt)

            # Persist ScheduledEvent to PostgreSQL database
            async with async_session() as session:
                db_event = ScheduledEvent(
                    id=discord_event.id,
                    guild_id=guild.id,
                    broadcast_channel_id=broadcast_channel.id
                    if broadcast_channel
                    else guild.id,
                    broadcast_message_id=broadcast_msg.id if broadcast_msg else None,
                    name=event_data.name,
                    description=event_data.description,
                    location=loc_str,
                    start_time=start_dt,
                    end_time=end_dt,
                    event_url=event_url,
                    reminder_intervals=pruned_intervals,
                    reminders_sent=[],
                    template_name="default_reminder.j2",
                    target_role_id=None,
                    is_active=True,
                )
                session.add(db_event)
                await session.commit()

            channel_mention = (
                f"<#{broadcast_channel.id}>"
                if broadcast_channel
                else "channel pengumuman"
            )
            return (
                f"✅ Acara '{event_data.name}' berhasil dijadwalkan dan disiarkan ke {channel_mention}!\n"
                f"🗓️ Waktu: {format_indonesian_date(start_dt)} pukul {format_time_wib(start_dt)} WIB\n"
                f"📍 Lokasi: {loc_str}\n"
                f"🔗 Link Event: {event_url}"
            )

        except Exception as e:
            # Error can come from Pydantic (wrong format) or Discord API (400 Bad Request, past time, etc.)
            return f"❌ Failed to create event. Error: {str(e)} (If this is a 'Cannot schedule event in the past' error, it means you set the wrong time/date, make sure to set a future time)."

    async def end_event_handler(self, arguments: dict, ctx_obj=None) -> str:
        """Handler to end/stop a Discord Scheduled Event via tool calling"""
        try:
            req_data = EndDiscordEventSchema.model_validate(arguments)
            if not self.bot.guilds:
                return "❌ Failed: Bot is not currently in any server."
            guild = (
                getattr(ctx_obj, "guild", self.bot.guilds[0])
                if ctx_obj
                else self.bot.guilds[0]
            )

            target_event = None
            if req_data.event_id:
                target_event = guild.get_scheduled_event(req_data.event_id)
                if not target_event:
                    try:
                        target_event = await guild.fetch_scheduled_event(
                            req_data.event_id
                        )
                    except Exception:
                        target_event = None
            else:
                events = list(guild.scheduled_events)
                if not events:
                    try:
                        events = await guild.fetch_scheduled_events()
                    except Exception:
                        events = []

                active_events = [
                    e for e in events if e.status == discord.EventStatus.active
                ]
                if active_events:
                    target_event = active_events[0]
                elif events:
                    target_event = events[0]

            if not target_event:
                return "❌ Tidak ditemukan acara aktif atau terjadwal di server untuk diakhiri."

            # End event in Discord API
            try:
                await target_event.end()
            except Exception as api_err:
                logger.warning(
                    f"Could not end event directly via target_event.end(): {api_err}"
                )

            # Update DB state
            async with async_session() as session:
                result = await session.execute(
                    select(ScheduledEvent).where(ScheduledEvent.id == target_event.id)
                )
                db_event = result.scalar_one_or_none()
                if db_event:
                    db_event.is_active = False
                    await session.commit()

            # Send broadcast completed if channel available
            announcement_channel_id = int(
                os.environ.get("ANNOUNCEMENT_CHANNEL_ID", "0")
            )
            broadcast_channel = None
            if announcement_channel_id:
                broadcast_channel = self.bot.get_channel(announcement_channel_id)
            if not broadcast_channel:
                broadcast_channel = getattr(ctx_obj, "channel", guild.system_channel)

            if broadcast_channel:
                try:
                    loc_name = target_event.location or (
                        target_event.channel.name if target_event.channel else ""
                    )
                    comp_text = render_event_template(
                        "events/broadcast_completed.j2",
                        {
                            "event": {
                                "name": target_event.name,
                                "location": loc_name,
                                "event_url": f"https://discord.com/events/{guild.id}/{target_event.id}",
                            },
                            "role_mention": None,
                        },
                    )
                    await broadcast_channel.send(comp_text)
                except Exception as c_err:
                    logger.error(f"Failed to send broadcast completed message: {c_err}")

            return f"✅ Acara '{target_event.name}' berhasil diakhiri dan ditutup dari daftar server."

        except Exception as e:
            return f"❌ Gagal mengakhiri acara. Error: {str(e)}"

    async def create_thread_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not ctx_obj:
                return "❌ Failed to create thread: ctx_obj not found (bot doesn't know which channel to create the thread in)."

            thread_data = DiscordThreadSchema.model_validate(arguments)
            channel = ctx_obj.channel

            # Can only create threads in a Text Channel
            if not isinstance(channel, discord.TextChannel):
                return "❌ Failed to create thread: This command can only be used in regular Text Channels."

            # Create thread, auto archive 10080 minutes (1 week)
            thread = await channel.create_thread(
                name=thread_data.name,
                type=discord.ChannelType.public_thread,
                auto_archive_duration=10080,
                reason=thread_data.reason,
            )

            return f"✅ Successfully created a thread named '{thread.name}'. Invite the user to continue the chat in that thread: <#{thread.id}>."

        except Exception as e:
            return f"❌ Failed to create thread. Error: {str(e)}"

    async def create_poll_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not ctx_obj:
                return "❌ Failed to create poll: ctx_obj not found."

            poll_data = DiscordPollSchema.model_validate(arguments)
            channel = ctx_obj.channel

            if len(poll_data.options) > 10:
                return "❌ Failed: Maximum poll options is 10."

            duration = timedelta(hours=min(poll_data.duration_hours, 168))
            poll = discord.Poll(
                question=poll_data.question,
                duration=duration,
                multiple=poll_data.allow_multiselect,
            )
            for opt in poll_data.options:
                poll.add_answer(text=opt)

            await channel.send(poll=poll)
            return f"✅ Successfully created a poll with the question: '{poll_data.question}'"
        except Exception as e:
            return f"❌ Failed to create poll. Error: {str(e)}"

    async def end_poll_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not ctx_obj:
                return "❌ Failed to end poll: ctx_obj not found."

            schema = EndDiscordPollSchema.model_validate(arguments)
            channel = ctx_obj.channel

            target_msg = None
            if schema.message_id:
                try:
                    target_msg = await channel.fetch_message(schema.message_id)
                except discord.NotFound:
                    return f"❌ Message with ID {schema.message_id} was not found in this channel."
            else:
                # Search recent messages for an active poll
                async for msg in channel.history(limit=50):
                    if msg.poll and not msg.poll.is_finalised():
                        target_msg = msg
                        break

            if not target_msg or not target_msg.poll:
                return "❌ No active poll found in this channel to end. If you have the specific message ID, please specify it."

            if target_msg.poll.is_finalised():
                return f"ℹ️ The poll '{target_msg.poll.question}' has already been closed/finalized."

            # End the poll early
            ended_msg = await target_msg.end_poll()
            poll = ended_msg.poll or target_msg.poll

            result_lines = []
            for ans in poll.answers:
                result_lines.append(f"• **{ans.text}**: {ans.vote_count} votes")

            results_str = "\n".join(result_lines)
            return (
                f"✅ Successfully ended the poll: **'{poll.question}'**\n\n"
                f"📊 **Final Results:**\n{results_str}"
            )
        except discord.Forbidden:
            return "❌ I don't have permission to end this poll (requires 'Manage Messages' permission or bot must be the creator)."
        except Exception as e:
            return f"❌ Failed to end poll. Error: {str(e)}"

    async def check_voice_channel_handler(self, arguments: dict, ctx_obj=None) -> str:
        try:
            schema = CheckVoiceChannelSchema.model_validate(arguments)
            if not ctx_obj or not ctx_obj.guild:
                return "❌ Cannot check voice channel because the server (guild) context was not found."

            target_vc = None

            # 1. Search by channel_name if specified
            if schema.channel_name and schema.channel_name.strip():
                c_name = schema.channel_name.lower().strip()
                for vc in ctx_obj.guild.voice_channels:
                    if c_name in vc.name.lower():
                        target_vc = vc
                        break

            # 2. Fallback to current channel if it is a Voice/Stage Channel (Voice Chat text channel)
            if not target_vc and hasattr(ctx_obj, "channel"):
                if isinstance(
                    ctx_obj.channel, (discord.VoiceChannel, discord.StageChannel)
                ):
                    target_vc = ctx_obj.channel

            # 3. Fallback to the user's currently connected Voice Channel
            if not target_vc:
                user_obj = getattr(ctx_obj, "author", getattr(ctx_obj, "user", None))
                if (
                    user_obj
                    and hasattr(user_obj, "voice")
                    and user_obj.voice
                    and user_obj.voice.channel
                ):
                    target_vc = user_obj.voice.channel

            if not target_vc:
                if schema.channel_name:
                    return f"❌ Voice Channel containing the word '{schema.channel_name}' was not found."
                return "❌ No voice channel specified, and you are not currently in a voice channel nor typing inside a voice channel text chat."

            members = target_vc.members
            if not members:
                return f"ℹ️ Currently, there is no one in the Voice Channel '{target_vc.name}'."

            member_list = [f"- {m.display_name} ({m.name})" for m in members]
            return (
                f"✅ List of people currently in the Voice Channel '{target_vc.name}' ({len(members)} people):\n"
                + "\n".join(member_list)
            )

        except Exception as e:
            logger.error(f"Error in check_voice_channel_handler: {e}")
            return f"❌ Failed to check voice channel: {str(e)}"

    async def get_channels_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not self.bot.guilds:
                return "❌ Error: Bot is not in any server."
            guild = self.bot.guilds[0]

            channels_info = []
            for c in guild.channels:
                if isinstance(c, discord.CategoryChannel):
                    continue
                channels_info.append(
                    {"id": str(c.id), "name": c.name, "type": str(c.type)}
                )
            return json.dumps(channels_info, indent=2)
        except Exception as e:
            return f"❌ Failed to get channel list: {str(e)}"

    async def get_roles_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not self.bot.guilds:
                return "❌ Error: Bot is not in any server."
            guild = self.bot.guilds[0]

            roles_info = [
                {"id": str(r.id), "name": r.name}
                for r in guild.roles
                if r.name != "@everyone"
            ]
            return json.dumps(roles_info, indent=2)
        except Exception as e:
            return f"❌ Failed to get role list: {str(e)}"

    async def clear_messages_handler(self, arguments: dict, ctx_obj=None):
        try:
            if not ctx_obj:
                return "❌ Failed: ctx_obj not found."

            if not ctx_obj.author.guild_permissions.manage_messages:
                return "❌ DENIED: User does not have 'Manage Messages' permission."

            req_data = ClearMessagesSchema.model_validate(arguments)
            limit = min(req_data.limit, 500)

            asyncio.create_task(
                self._background_delete(ctx_obj.channel, limit, req_data.only_today)
            )
            return f"✅ Processing message deletion (Limit: {limit}, Only Today: {req_data.only_today}) in the background. Tell the user to wait a moment."

        except Exception as e:
            return f"❌ Failed to process clear_messages: {str(e)}"

    async def _background_delete(self, channel, limit: int, only_today: bool):
        try:
            # Use discord.utils.utcnow() to avoid timezone offset-naive errors
            today_start = discord.utils.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            def check_msg(msg):
                if only_today:
                    return msg.created_at >= today_start
                return True

            # channel.purge() automatically handles bulk_delete (<14 days) and single delete (>14 days)
            deleted = await channel.purge(limit=limit + 2, check=check_msg)
            logger.info(
                f"Successfully deleted {len(deleted)} messages in channel {channel.name}."
            )
        except discord.Forbidden:
            logger.error(
                "Failed to delete messages: Bot does not have Manage Messages permission."
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to delete messages (HTTP Exception): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during message purge: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send a welcome message when a new member joins"""
        channel_id = int(os.environ.get("WELCOME_AND_RULES_CHANNEL_ID", 0))
        channel = self.bot.get_channel(channel_id)

        if channel:
            welcome_msg = (
                f"Welcome {member.mention} to the AIoT server! 👋\n"
                f"To get more access, please introduce yourself using the following format:\n\n"
                f"Name:\n"
                f"Nickname:\n"
                f"Batch/Year:\n"
                f"Hobby:\n"
                f"Interest:\n"
            )
            await channel.send(welcome_msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Check messages in a specific channel to automatically assign roles"""
        # Ignore messages from the bot itself
        if message.author.bot:
            return

        channel_id = int(os.environ.get("WELCOME_AND_RULES_CHANNEL_ID", 0))
        # Only monitor messages in the welcome-and-rules channel
        if message.channel.id == channel_id:
            content = message.content.lower()

            # Check if all introduction format keywords are present in the message
            keywords = ["name:", "nickname:", "batch/year:", "hobby:", "interest:"]
            if all(keyword in content for keyword in keywords):
                # Find the 'Member' role in the server
                role = discord.utils.get(message.guild.roles, name="Member")

                if role:
                    try:
                        await message.author.add_roles(role)
                        await message.add_reaction("👋")

                        # Extract Nickname using regex
                        match = re.search(
                            r"nickname:\s*(.+)", message.content, re.IGNORECASE
                        )
                        if match:
                            nickname = match.group(1).strip()
                            await message.reply(
                                f"{message.author.mention} Nice to meet you, {nickname}! Welcome to KSM AIoT!"
                            )
                        else:
                            await message.reply(
                                f"{message.author.mention} Nice to meet you! Welcome to KSM AIoT!"
                            )
                    except discord.Forbidden:
                        # Bot lacks Manage Roles permission
                        await message.reply(
                            "⚠️ The KSM AIoT Bot tried to assign a role, but it does not have permission (Permission: Manage Roles)."
                        )
                    except Exception as e:
                        logger.error(f"Error when assigning role: {e}")
                else:
                    await message.reply(
                        "⚠️ The 'Member' role was not found on this server. Please tell the admin to create it."
                    )

    @tasks.loop(seconds=60)
    async def reminder_loop(self):
        """Background task checking scheduled event reminders, auto-start, and auto-end every 60s"""
        try:
            now_utc = datetime.now(timezone.utc)
            async with async_session() as session:
                result = await session.execute(
                    select(ScheduledEvent).where(
                        ScheduledEvent.is_active == True,  # noqa: E712
                    )
                )
                active_events = result.scalars().all()

                for ev in active_events:
                    expiry_time = ev.end_time or (ev.start_time + timedelta(hours=2))

                    # Get Discord guild and ScheduledEvent object
                    guild = self.bot.get_guild(ev.guild_id) or (
                        self.bot.guilds[0] if self.bot.guilds else None
                    )
                    discord_event = None
                    if guild:
                        discord_event = guild.get_scheduled_event(ev.id)
                        if not discord_event:
                            try:
                                discord_event = await guild.fetch_scheduled_event(ev.id)
                            except Exception:
                                discord_event = None

                    # 1. AUTO-END: Check if event has ended
                    if now_utc >= expiry_time:
                        if discord_event and discord_event.status in (
                            discord.EventStatus.active,
                            discord.EventStatus.scheduled,
                        ):
                            try:
                                await discord_event.end()
                                logger.info(
                                    f"Auto-ended scheduled event {ev.id} ({ev.name})"
                                )
                            except Exception as end_err:
                                logger.warning(
                                    f"Could not auto-end discord event {ev.id}: {end_err}"
                                )

                            # Broadcast completion message
                            channel = self.bot.get_channel(ev.broadcast_channel_id)
                            if channel:
                                comp_ctx = {
                                    "event": {
                                        "name": ev.name,
                                        "location": ev.location,
                                        "event_url": ev.event_url,
                                    },
                                    "role_mention": f"<@&{ev.target_role_id}>"
                                    if ev.target_role_id
                                    else None,
                                }
                                try:
                                    comp_text = render_event_template(
                                        "events/broadcast_completed.j2", comp_ctx
                                    )
                                    await channel.send(comp_text)
                                except Exception as comp_err:
                                    logger.error(
                                        f"Failed to send completion broadcast: {comp_err}"
                                    )

                        ev.is_active = False
                        continue

                    # 2. AUTO-START: Check if event start time has arrived
                    if (
                        discord_event
                        and discord_event.status == discord.EventStatus.scheduled
                        and now_utc >= ev.start_time
                    ):
                        if discord_event.channel:
                            try:
                                await discord_event.start()
                                logger.info(
                                    f"Auto-started scheduled event {ev.id} ({ev.name})"
                                )
                                # Broadcast started message
                                channel = self.bot.get_channel(ev.broadcast_channel_id)
                                if channel:
                                    start_ctx = {
                                        "event": {
                                            "name": ev.name,
                                            "location": ev.location,
                                            "event_url": ev.event_url,
                                        },
                                        "role_mention": f"<@&{ev.target_role_id}>"
                                        if ev.target_role_id
                                        else None,
                                    }
                                    try:
                                        start_text = render_event_template(
                                            "events/broadcast_started.j2",
                                            start_ctx,
                                        )
                                        await channel.send(start_text)
                                    except Exception as start_err:
                                        logger.error(
                                            f"Failed to send started broadcast: {start_err}"
                                        )
                            except Exception as start_api_err:
                                logger.warning(
                                    f"Could not auto-start discord event {ev.id}: {start_api_err}"
                                )

                    # 3. MULTI-INTERVAL REMINDERS: Check due reminder intervals
                    intervals = ev.reminder_intervals or []
                    sent = list(ev.reminders_sent or [])
                    dirty = False

                    for interval in intervals:
                        if interval in sent:
                            continue
                        trigger_time = ev.start_time - timedelta(minutes=interval)
                        if now_utc >= trigger_time:
                            channel = self.bot.get_channel(ev.broadcast_channel_id)
                            if not channel:
                                try:
                                    channel = await self.bot.fetch_channel(
                                        ev.broadcast_channel_id
                                    )
                                except Exception:
                                    channel = None

                            if channel:
                                time_label = get_human_time_label(interval)
                                ctx = {
                                    "event": {
                                        "name": ev.name,
                                        "description": ev.description or "",
                                        "location": ev.location,
                                        "event_url": ev.event_url,
                                    },
                                    "time_label": time_label,
                                    "formatted_time": format_time_wib(ev.start_time),
                                    "role_mention": f"<@&{ev.target_role_id}>"
                                    if ev.target_role_id
                                    else None,
                                }
                                try:
                                    reminder_text = render_event_template(
                                        ev.template_name
                                        or "events/default_reminder.j2",
                                        ctx,
                                    )
                                    await channel.send(reminder_text)
                                except Exception as send_err:
                                    logger.error(
                                        f"Failed to send reminder for event {ev.id}: {send_err}"
                                    )

                            sent.append(interval)
                            dirty = True

                    if dirty:
                        ev.reminders_sent = sent
                        flag_modified(ev, "reminders_sent")

                await session.commit()
        except Exception as e:
            logger.error(f"Error in reminder_loop: {e}")

    @reminder_loop.before_loop
    async def before_reminder_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_scheduled_event_update(
        self, before: discord.ScheduledEvent, after: discord.ScheduledEvent
    ):
        """Gateway listener to sync event updates (anti data-drift)"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(ScheduledEvent).where(ScheduledEvent.id == after.id)
                )
                db_event = result.scalar_one_or_none()
                if not db_event:
                    return

                if after.status in (
                    discord.EventStatus.completed,
                    discord.EventStatus.cancelled,
                ):
                    db_event.is_active = False
                else:
                    db_event.name = after.name
                    db_event.description = after.description
                    if after.location:
                        db_event.location = after.location
                    elif after.channel:
                        db_event.location = after.channel.name

                    if after.start_time and after.start_time != db_event.start_time:
                        db_event.start_time = after.start_time
                        # Re-prune intervals for updated start time
                        db_event.reminder_intervals = prune_reminder_intervals(
                            after.start_time
                        )
                        # Reset sent reminders whose triggers are now in the future
                        now_utc = datetime.now(timezone.utc)
                        db_event.reminders_sent = [
                            i
                            for i in (db_event.reminders_sent or [])
                            if now_utc >= (after.start_time - timedelta(minutes=i))
                        ]
                        flag_modified(db_event, "reminder_intervals")
                        flag_modified(db_event, "reminders_sent")

                    if after.end_time:
                        db_event.end_time = after.end_time

                await session.commit()
        except Exception as e:
            logger.error(f"Error handling scheduled event update: {e}")

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        """Gateway listener to stop reminders when an event is deleted"""
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(ScheduledEvent).where(ScheduledEvent.id == event.id)
                )
                db_event = result.scalar_one_or_none()
                if db_event:
                    db_event.is_active = False
                    await session.commit()
        except Exception as e:
            logger.error(f"Error handling scheduled event delete: {e}")


async def setup(bot):
    await bot.add_cog(ServerEvents(bot))
