import logging
import re

import discord
from discord import ui

from config.settings import settings

logger = logging.getLogger("onboarding")


class IntroModal(ui.Modal, title="Form Perkenalan KSM AIoT"):
    nickname = ui.Label(
        text="Nickname",
        component=ui.TextInput(placeholder="Contoh: John"),
        description="Nama panggilan yang akan digunakan di server.",
    )
    id_number = ui.Label(
        text="NIM / NIDN / NIP",
        component=ui.TextInput(placeholder="Contoh: 2210511084"),
        description="Nomor identitas (10 digit NIM/NIDN atau 18 digit NIP Dosen).",
    )
    batch = ui.Label(
        text="Angkatan / Batch",
        component=ui.TextInput(placeholder="Contoh: 2026", min_length=4, max_length=4),
        description="Tahun angkatan kamu.",
    )
    hobby_interest = ui.Label(
        text="Hobi & Minat",
        component=ui.TextInput(
            placeholder="Contoh: Machine Learning, IoT, Game Dev",
            style=discord.TextStyle.long,
        ),
        description="Hobi dan bidang minat yang sedang ditekuni.",
    )

    major_select = ui.Label(
        text="Choose your major",
        component=ui.Select(
            placeholder="Choose your major...",
            options=[
                discord.SelectOption(label="Informatics (IF)", value="IF"),
                discord.SelectOption(label="Information Systems (SI)", value="SI"),
                discord.SelectOption(
                    label="Information Systems Diploma (D3SI)", value="D3SI"
                ),
                discord.SelectOption(label="Data Science (DS)", value="DS"),
            ],
        ),
    )

    async def notify_pengurus(
        self,
        guild: discord.Guild,
        user: discord.Member,
        nickname: str,
        id_type: str,
        id_number: str,
        major: str,
        batch: str,
        intro_message: discord.Message | None,
    ) -> bool:
        channel = guild.get_channel(settings.PENGURUS_CHANNEL_ID)
        if channel is None:
            logger.error("PENGURUS_CHANNEL_ID is invalid or the channel was not found.")
            return False

        embed = discord.Embed(
            title="Lecturer Verification Required",
            description=f"{user.mention} submitted the introduction form as a lecturer.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Nickname", value=nickname, inline=True)
        embed.add_field(name=id_type, value=id_number, inline=True)
        embed.add_field(name="Major", value=major, inline=True)
        embed.add_field(name="Batch", value=batch, inline=True)
        embed.add_field(name="User ID", value=str(user.id), inline=True)
        if intro_message:
            embed.add_field(
                name="Introduction message",
                value=f"[View]({intro_message.jump_url})",
                inline=False,
            )
        embed.set_footer(text="Nexo Bot - KSM AIoT")

        content = None
        mentions = discord.AllowedMentions.none()
        if settings.PENGURUS_ROLE_ID:
            content = f"<@&{settings.PENGURUS_ROLE_ID}>"
            mentions = discord.AllowedMentions(
                roles=[discord.Object(id=settings.PENGURUS_ROLE_ID)]
            )

        try:
            await channel.send(content=content, embed=embed, allowed_mentions=mentions)
            return True
        except discord.HTTPException as error:
            logger.error("Failed to send admin notification: %s", error)
            return False

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user
        if guild is None:
            await interaction.followup.send(
                "⚠️ This form can only be used inside a server.", ephemeral=True
            )
            return

        id_number = self.id_number.component.value.strip()
        nickname = self.nickname.component.value.strip()
        major = self.major_select.component.values[0]
        batch = self.batch.component.value.strip()
        hobby_interest = self.hobby_interest.component.value

        if not re.fullmatch(r"[0-9]+", id_number):
            await interaction.followup.send(
                "⚠️ The identification number may only contain digits.",
                ephemeral=True,
            )
            return

        if len(id_number) not in (10, 18):
            await interaction.followup.send(
                "⚠️ ID must be a 10-digit NIM/NIDN or 18-digit NIP.",
                ephemeral=True,
            )
            return

        nim_match = re.fullmatch(r"([0-9]{2})10([0-9]{3})([0-9]{3})", id_number)
        is_nip = bool(re.fullmatch(r"[0-9]{18}", id_number))
        is_nidn = bool(re.fullmatch(r"[0-9]{10}", id_number)) and not nim_match

        if not (nim_match or is_nip or is_nidn):
            await interaction.followup.send(
                "⚠️ Invalid identification format. Enter a 10-digit NIM/NIDN "
                "or an 18-digit lecturer NIP.",
                ephemeral=True,
            )
            return

        if nim_match:
            year_short = nim_match.group(1)
            seq_num = nim_match.group(3)
            suffix = f" {major}'{year_short} {seq_num}"
        else:
            suffix = " [Lecturer]"

        new_nickname = nickname[: 32 - len(suffix)] + suffix
        warnings: list[str] = []
        role = (
            guild.get_role(settings.MEMBER_ROLE_ID) if settings.MEMBER_ROLE_ID else None
        )

        if role is None:
            logger.error("MEMBER_ROLE_ID is invalid or the role was not found.")
            warnings.append("The Member role was not found. Contact an administrator.")
        elif role not in user.roles:
            try:
                await user.add_roles(role, reason="KSM AIoT introduction form")
            except discord.Forbidden:
                warnings.append(
                    "The bot cannot assign the Member role. Contact an administrator."
                )
            except discord.HTTPException as error:
                logger.error("Failed to assign the Member role: %s", error)
                warnings.append("The Member role could not be assigned.")

        if user.nick != new_nickname:
            try:
                await user.edit(nick=new_nickname, reason="KSM AIoT introduction form")
            except discord.Forbidden:
                warnings.append(
                    "The nickname could not be changed automatically; "
                    "the user's role may be higher than the bot's role."
                )
            except discord.HTTPException as error:
                logger.error("Failed to update nickname: %s", error)
                warnings.append("The nickname could not be updated.")

        if nim_match:
            formatted_intro = (
                f"**Nickname:** {nickname}\n"
                f"**NIM:** {id_number}\n"
                f"**Major:** {major}\n"
                f"**Batch:** {batch}\n"
                f"**Hobbies and Interests:** {hobby_interest}"
            )
        else:
            formatted_intro = (
                f"**Nickname:** {nickname}\n"
                f"**Major:** {major}\n"
                f"**Batch:** {batch}\n"
                f"**Hobbies and Interests:** {hobby_interest}"
            )

        pub_message = None
        try:
            pub_message = await interaction.channel.send(
                content=formatted_intro,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await pub_message.add_reaction("👋")
            await pub_message.reply(
                f"Nice to meet you, {user.mention}! Welcome to KSM AIoT! 🚀",
                allowed_mentions=discord.AllowedMentions(users=[user]),
            )
        except discord.Forbidden:
            warnings.append("The bot cannot send messages in this channel.")
        except discord.HTTPException as error:
            logger.error("Failed to send introduction: %s", error)
            warnings.append("The introduction could not be sent to the channel.")

        if warnings:
            msg = "⚠️ The form was processed with some issues:\n- " + "\n- ".join(
                warnings
            )
        else:
            msg = "Your introduction form was submitted successfully!"
            if not nim_match:
                msg += "\nAn administrator will assign the Lecturer role after verification."
                id_type = "NIP" if is_nip else "NIDN"
                ok = await self.notify_pengurus(
                    guild, user, nickname, id_type, id_number, major, batch, pub_message
                )
                if not ok:
                    msg += "\nThe administrators were not notified; please contact them manually."

        await interaction.followup.send(msg, ephemeral=True)


class IntroView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Fill Introduction Form",
        style=discord.ButtonStyle.primary,
        custom_id="intro_form_button",
    )
    async def open_intro_modal(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.send_modal(IntroModal())
