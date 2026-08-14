import discord
import os
import logging
import re
import json
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

from utils.schemas import (
    DiscordEventSchema,
    DiscordThreadSchema,
    DiscordPollSchema,
    GetServerChannelsSchema,
    GetServerRolesSchema,
    ClearMessagesSchema,
    CheckVoiceChannelSchema,
)

logger = logging.getLogger("server_events")


class ServerEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                "create_discord_thread",
                "create_discord_poll",
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
                    "description": "Schedule a new Discord Event (Event/Meeting) on the Server. This tool requires the time (date & time WIB) and event description.",
                    "parameters": DiscordEventSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["create_discord_event"] = self.create_event_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "create_discord_thread",
                    "description": "Create a new Discord Thread in the user's current channel. Use this if the user asks to move the topic/discussion to a new thread.",
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
                    "description": "Create an interactive poll (Native Discord Poll) in the current channel.",
                    "parameters": DiscordPollSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["create_discord_poll"] = self.create_poll_handler

        self.bot.ai_tools.append(
            {
                "type": "function",
                "function": {
                    "name": "get_server_channels",
                    "description": "Get a list of all text and voice channels on this server. Very useful for finding out channel IDs and server structure.",
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
                    "description": "Get a list of all available roles on the server along with their IDs.",
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
                    "description": "Delete messages in bulk in the current channel. Can only be used if the user has 'Manage Messages' permission. Can filter to delete only today's messages.",
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
                    "description": "Check the list of users (members) currently in a specific Voice Channel.",
                    "parameters": CheckVoiceChannelSchema.model_json_schema(),
                },
            }
        )
        self.bot.local_tool_handlers["check_voice_channel"] = (
            self.check_voice_channel_handler
        )

    async def create_event_handler(self, arguments: dict, ctx_obj=None) -> str:
        """Function called by the LLM brain when the tool is used"""
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
                await guild.create_scheduled_event(
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
                await guild.create_scheduled_event(
                    name=event_data.name,
                    description=event_data.description,
                    start_time=start_dt,
                    end_time=end_dt,
                    entity_type=discord.EntityType.external,
                    location=event_data.location,
                    privacy_level=discord.PrivacyLevel.guild_only,
                )
                loc_str = event_data.location

            return f"✅ Successfully scheduled event '{event_data.name}' starting at {start_str} located at {loc_str}."

        except Exception as e:
            # Error can come from Pydantic (wrong format) or Discord API (400 Bad Request, past time, etc.)
            return f"❌ Failed to create event. Error: {str(e)} (If this is a 'Cannot schedule event in the past' error, it means you set the wrong time/date, make sure to set a future time)."

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
                f"Please introduce yourself using the following format:\n\n"
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


async def setup(bot):
    await bot.add_cog(ServerEvents(bot))
