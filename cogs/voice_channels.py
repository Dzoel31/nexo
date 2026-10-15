import logging

import discord
from discord.ext import commands

logger = logging.getLogger("voice_channels")


class VoiceChannelMixin:
    @commands.Cog.listener()
    async def on_ready(self):
        if self.has_vc_stage_scanned:
            return

        await self.bot.wait_until_ready()
        category = self.bot.get_channel(self.CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            logger.warning("CategoryChannel for voice channels was not found.")
            self.has_vc_stage_scanned = True
            return

        logger.info("Scanned and cached category ID: %s", category.id)
        cleaned_vc_count = recovered_vc_count = 0
        cleaned_stage_count = recovered_stage_count = 0

        for channel in category.voice_channels:
            if channel.id == self.GENERATOR_CHANNEL_ID or not channel.name.startswith(
                "🔒 "
            ):
                continue
            if len(channel.members) == 0:
                try:
                    await channel.delete(reason="Clean up empty temporary channel")
                    cleaned_vc_count += 1
                except discord.HTTPException:
                    pass
            else:
                self.active_temp_channels.add(channel.id)
                recovered_vc_count += 1

        for stage in category.stage_channels:
            if stage.id == self.GENERATOR_STAGE_ID or not stage.name.startswith("🎙️ "):
                continue
            if len(stage.members) == 0:
                try:
                    await stage.delete(reason="Clean up empty temporary stage")
                    cleaned_stage_count += 1
                except discord.HTTPException:
                    pass
            else:
                self.active_temp_channels.add(stage.id)
                recovered_stage_count += 1

        logger.info("Cleaned %s empty temporary voice channels", cleaned_vc_count)
        logger.info("Recovered %s active temporary voice channels", recovered_vc_count)
        logger.info("Cleaned %s empty temporary stages", cleaned_stage_count)
        logger.info("Recovered %s active temporary stages", recovered_stage_count)
        self.has_vc_stage_scanned = True

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if after.channel and after.channel.id in (
            self.GENERATOR_CHANNEL_ID,
            self.GENERATOR_STAGE_ID,
        ):
            guild = member.guild
            category = after.channel.category
            overwrites = category.overwrites.copy() if category else {}
            overwrites[member] = discord.PermissionOverwrite(
                manage_channels=True,
                move_members=True,
                manage_permissions=True,
                **(
                    {"mute_members": True}
                    if after.channel.id == self.GENERATOR_STAGE_ID
                    else {}
                ),
            )

            try:
                if after.channel.id == self.GENERATOR_STAGE_ID:
                    temp_channel = await guild.create_stage_channel(
                        name=f"🎙 {member.display_name}'s Stage",
                        category=category,
                        overwrites=overwrites,
                    )
                else:
                    temp_channel = await guild.create_voice_channel(
                        name=f"🔒 {member.display_name}'s Room",
                        category=category,
                        overwrites=overwrites,
                    )
                self.active_temp_channels.add(temp_channel.id)
                await member.move_to(temp_channel)
            except discord.HTTPException as error:
                logger.error("Failed to create temporary channel: %s", error)
                return

        if (
            before.channel
            and before.channel.id in self.active_temp_channels
            and len(before.channel.members) == 0
        ):
            try:
                self.active_temp_channels.remove(before.channel.id)
                await before.channel.delete(reason="Temporary channel is empty")
            except discord.NotFound:
                pass
            except discord.HTTPException as error:
                logger.error("Failed to delete temporary channel: %s", error)
