import asyncio
import logging
from datetime import datetime, timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands, tasks
from db.repository import (
    create_competition,
    delete_competition,
    get_competition_by_id,
    list_active_competitions,
    update_competition_reminders,
)
from utils.auth_helper import has_permission

logger = logging.getLogger("competition_radar")

WIB = timezone(timedelta(hours=7))

CATEGORIES = [
    app_commands.Choice(name="🤖 Artificial Intelligence (AI)", value="AI"),
    app_commands.Choice(name="📡 Internet of Things (IoT)", value="IoT"),
    app_commands.Choice(name="💻 Web & Mobile Development", value="Web/Mobile"),
    app_commands.Choice(name="📊 Data Science & Analytics", value="Data Science"),
    app_commands.Choice(name="🏆 Gemastik / PKM / Nasional", value="Gemastik/PKM"),
    app_commands.Choice(name="🌐 Umum & Lainnya", value="Umum"),
]


def parse_deadline_wib(deadline_str: str) -> datetime | None:
    """
    Parses deadline string assumed in WIB (UTC+7):
    Supports 'YYYY-MM-DD HH:MM', 'YYYY-MM-DD', 'DD-MM-YYYY HH:MM', 'DD-MM-YYYY'.
    Returns UTC datetime.
    """
    formats = (
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d_%H:%M",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(deadline_str.strip(), fmt)
            if fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                # Default end of day: 23:59 WIB
                dt = dt.replace(hour=23, minute=59, second=59)
            dt_wib = dt.replace(tzinfo=WIB)
            return dt_wib.astimezone(timezone.utc)
        except ValueError:
            pass
    return None


class CompetitionView(discord.ui.View):
    def __init__(self, reg_url: str | None = None, guide_url: str | None = None):
        super().__init__(timeout=None)
        if reg_url:
            self.add_item(
                discord.ui.Button(
                    label="📝 Link Pendaftaran",
                    url=reg_url,
                    style=discord.ButtonStyle.link,
                )
            )
        if guide_url:
            self.add_item(
                discord.ui.Button(
                    label="📖 Buku Panduan",
                    url=guide_url,
                    style=discord.ButtonStyle.link,
                )
            )


class CompetitionRadar(commands.Cog):
    """Cog for managing competitions, hackathons, and deadline countdown reminders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deadline_reminder_loop.start()

    def cog_unload(self):
        self.deadline_reminder_loop.cancel()

    lomba_group = app_commands.Group(
        name="lomba",
        description="Radar kompetisi, hackathon, dan pengingat deadline KSM AIoT",
    )

    @lomba_group.command(
        name="add",
        description="Daftarkan info kompetisi/hackathon baru ke radar KSM",
    )
    @app_commands.choices(kategori=CATEGORIES)
    @app_commands.describe(
        nama="Nama kompetisi / hackathon (contoh: Gemastik XIX 2026)",
        deadline="Batas pendaftaran (contoh: 2026-10-15 23:59 atau 2026-10-15)",
        kategori="Kategori bidang kompetisi",
        link_pendaftaran="URL halaman pendaftaran kompetisi (opsional)",
        link_panduan="URL buku panduan / guidebook lomba (opsional)",
        deskripsi="Keterangan singkat, syarat, atau tema lomba (opsional)",
        channel="Channel teks untuk broadcast reminder (default: channel aktif)",
        role="Role yang akan dimention saat countdown darurat (opsional)",
    )
    async def add_competition(
        self,
        interaction: discord.Interaction,
        nama: str,
        deadline: str,
        kategori: app_commands.Choice[str],
        link_pendaftaran: str | None = None,
        link_panduan: str | None = None,
        deskripsi: str | None = None,
        channel: discord.TextChannel | None = None,
        role: discord.Role | None = None,
    ):
        if not has_permission(
            interaction,
            "manage_messages",
            allowed_roles=["Leader", "Co-Leader", "Staff-Core", "Admin"],
        ):
            return await interaction.response.send_message(
                "❌ **Akses Ditolak**: Anda tidak memiliki izin mendaftarkan kompetisi.",
                ephemeral=True,
            )

        deadline_utc = parse_deadline_wib(deadline)
        if not deadline_utc:
            return await interaction.response.send_message(
                "❌ Format tanggal deadline tidak valid!\n"
                "Gunakan format: `YYYY-MM-DD HH:MM` atau `YYYY-MM-DD` (contoh: `2026-10-01 23:59`).",
                ephemeral=True,
            )

        now_utc = datetime.now(timezone.utc)
        if deadline_utc <= now_utc:
            return await interaction.response.send_message(
                "⚠️ Tanggal deadline harus berada di masa depan!",
                ephemeral=True,
            )

        target_channel = channel or interaction.channel
        comp = await create_competition(
            guild_id=interaction.guild_id,
            name=nama.strip(),
            category=kategori.value,
            deadline=deadline_utc,
            channel_id=target_channel.id,
            created_by=interaction.user.id,
            registration_url=link_pendaftaran.strip() if link_pendaftaran else None,
            guidebook_url=link_panduan.strip() if link_panduan else None,
            description=deskripsi.strip() if deskripsi else None,
            target_role_id=role.id if role else None,
        )

        ts = int(deadline_utc.timestamp())
        embed = discord.Embed(
            title=f"🏆 Kompetisi Baru Terdaftar: {comp.name}",
            description=comp.description or "*Tidak ada deskripsi tambahan.*",
            color=discord.Color.gold(),
        )
        embed.add_field(name="📂 Kategori", value=comp.category, inline=True)
        embed.add_field(
            name="⏰ Batas Pendaftaran",
            value=f"<t:{ts}:F>\n(<t:{ts}:R>)",
            inline=True,
        )
        embed.add_field(
            name="📢 Channel Info",
            value=target_channel.mention,
            inline=True,
        )
        if role:
            embed.add_field(name="🎯 Role Target", value=role.mention, inline=True)
        embed.set_footer(
            text=f"ID Lomba: {comp.id} • Didaftarkan oleh {interaction.user.display_name}"
        )

        view = CompetitionView(comp.registration_url, comp.guidebook_url)
        await interaction.response.send_message(embed=embed, view=view)

    @lomba_group.command(
        name="list",
        description="Tampilkan daftar seluruh kompetisi & hackathon yang sedang aktif",
    )
    @app_commands.choices(kategori=CATEGORIES)
    @app_commands.describe(kategori="Filter berdasarkan kategori bidang (opsional)")
    async def list_competitions(
        self,
        interaction: discord.Interaction,
        kategori: app_commands.Choice[str] | None = None,
    ):
        competitions = await list_active_competitions(interaction.guild_id)
        if kategori:
            competitions = [c for c in competitions if c.category == kategori.value]

        if not competitions:
            filter_text = f" untuk kategori `{kategori.name}`" if kategori else ""
            return await interaction.response.send_message(
                f"ℹ️ Belum ada kompetisi aktif yang terdaftar di radar{filter_text}.",
                ephemeral=True,
            )

        embed = discord.Embed(
            title="📡 Radar Kompetisi & Hackathon KSM AIoT",
            description="Berikut adalah agenda perlombaan teknologi yang sedang membuka pendaftaran:",
            color=discord.Color.from_rgb(0, 168, 252),
        )

        for comp in competitions[:12]:
            ts = int(comp.deadline.timestamp())
            links = []
            if comp.registration_url:
                links.append(f"[Daftar]({comp.registration_url})")
            if comp.guidebook_url:
                links.append(f"[Guidebook]({comp.guidebook_url})")
            link_str = " • ".join(links) if links else "Link belum tersedia"

            embed.add_field(
                name=f"#{comp.id} | {comp.name} [{comp.category}]",
                value=f"• **Deadline:** <t:{ts}:R> (<t:{ts}:d>)\n• **Info:** {link_str}",
                inline=False,
            )

        embed.set_footer(
            text=f"Total: {len(competitions)} kompetisi aktif • Gunakan /lomba detail <id> untuk info lengkap"
        )
        await interaction.response.send_message(embed=embed)

    @lomba_group.command(
        name="detail",
        description="Tampilkan rincian lengkap informasi suatu kompetisi",
    )
    @app_commands.describe(id="ID kompetisi yang ingin dilihat")
    async def detail_competition(self, interaction: discord.Interaction, id: int):
        comp = await get_competition_by_id(id, interaction.guild_id)
        if not comp or not comp.is_active:
            return await interaction.response.send_message(
                f"❌ Kompetisi dengan ID `#{id}` tidak ditemukan atau sudah ditutup.",
                ephemeral=True,
            )

        ts = int(comp.deadline.timestamp())
        ch = interaction.guild.get_channel(comp.channel_id)
        ch_text = ch.mention if ch else f"`{comp.channel_id}`"

        embed = discord.Embed(
            title=f"🏆 {comp.name}",
            description=comp.description or "*Tidak ada deskripsi tambahan.*",
            color=discord.Color.blue(),
        )
        embed.add_field(name="📂 Kategori", value=comp.category, inline=True)
        embed.add_field(name="📢 Channel Target", value=ch_text, inline=True)
        embed.add_field(
            name="⏰ Batas Waktu",
            value=f"<t:{ts}:F>\n**Sisa Waktu:** <t:{ts}:R>",
            inline=False,
        )

        if comp.target_role_id:
            role = interaction.guild.get_role(comp.target_role_id)
            if role:
                embed.add_field(name="🎯 Role", value=role.mention, inline=True)

        reminders_text = (
            ", ".join(f"H-{r}" for r in sorted(comp.reminders_sent, reverse=True))
            if comp.reminders_sent
            else "Belum ada"
        )
        embed.add_field(name="🔔 Reminder Terkirim", value=reminders_text, inline=True)
        embed.set_footer(text=f"ID Lomba: {comp.id} • KSM AIoT Competition Radar")

        view = CompetitionView(comp.registration_url, comp.guidebook_url)
        await interaction.response.send_message(embed=embed, view=view)

    @lomba_group.command(
        name="delete",
        description="Hapus atau nonaktifkan data kompetisi dari radar (Admin/Staff)",
    )
    @app_commands.describe(id="ID kompetisi yang ingin dihapus")
    async def delete_comp(self, interaction: discord.Interaction, id: int):
        if not has_permission(
            interaction,
            "manage_messages",
            allowed_roles=["Leader", "Co-Leader", "Staff-Core", "Admin"],
        ):
            return await interaction.response.send_message(
                "❌ **Akses Ditolak**: Anda tidak memiliki izin menghapus data kompetisi.",
                ephemeral=True,
            )

        success = await delete_competition(id, interaction.guild_id)
        if success:
            await interaction.response.send_message(
                f"✅ Data kompetisi `#{id}` berhasil dinonaktifkan dari radar.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Kompetisi dengan ID `#{id}` tidak ditemukan.",
                ephemeral=True,
            )

    @tasks.loop(minutes=30)
    async def deadline_reminder_loop(self):
        """Background task checking competition deadlines every 30 minutes."""
        try:
            now_utc = datetime.now(timezone.utc)
            for guild in self.bot.guilds:
                competitions = await list_active_competitions(guild.id)
                for comp in competitions:
                    delta = comp.deadline - now_utc
                    total_seconds = delta.total_seconds()

                    # Auto-close expired competitions
                    if total_seconds <= 0:
                        await delete_competition(comp.id, guild.id)
                        logger.info(
                            f"Auto-closed expired competition #{comp.id} ({comp.name})"
                        )
                        continue

                    days_left = total_seconds / 86400.0
                    sent_list = list(comp.reminders_sent or [])

                    # Reminder milestones: H-1, H-3, H-7
                    target_milestone = None
                    if days_left <= 1.0 and 1 not in sent_list:
                        target_milestone = 1
                    elif days_left <= 3.0 and 3 not in sent_list:
                        target_milestone = 3
                    elif days_left <= 7.0 and 7 not in sent_list:
                        target_milestone = 7

                    if target_milestone is not None:
                        channel = guild.get_channel(comp.channel_id)
                        if channel:
                            ts = int(comp.deadline.timestamp())
                            role_mention = (
                                f"<@&{comp.target_role_id}>"
                                if comp.target_role_id
                                else None
                            )

                            if target_milestone == 1:
                                color = discord.Color.red()
                                alert_prefix = "🚨 **[H-1 LAST CALL DEADLINE LOMBA]**"
                            elif target_milestone == 3:
                                color = discord.Color.orange()
                                alert_prefix = "⚠️ **[H-3 REMINDER DEADLINE LOMBA]**"
                            else:
                                color = discord.Color.gold()
                                alert_prefix = "📢 **[H-7 REMINDER PERSIAPAN LOMBA]**"

                            embed = discord.Embed(
                                title=f"{alert_prefix} {comp.name}",
                                description=(
                                    f"Batas akhir pendaftaran tersisa **{target_milestone} hari lagi**!\n"
                                    f"Pastikan berkas proposal, tim, dan administrasi telah dipersiapkan.\n\n"
                                    f"⏰ **Batas Waktu:** <t:{ts}:F> (<t:{ts}:R>)\n"
                                    f"📂 **Kategori:** `{comp.category}`"
                                ),
                                color=color,
                            )
                            embed.set_footer(
                                text=f"ID Lomba: {comp.id} • KSM AIoT Competition Radar"
                            )
                            view = CompetitionView(
                                comp.registration_url, comp.guidebook_url
                            )

                            allowed_mentions = discord.AllowedMentions(
                                roles=True, everyone=True, users=True
                            )
                            await channel.send(
                                content=role_mention,
                                embed=embed,
                                view=view,
                                allowed_mentions=allowed_mentions,
                            )

                            sent_list.append(target_milestone)
                            await update_competition_reminders(comp.id, sent_list)
                            logger.info(
                                f"Sent H-{target_milestone} reminder for competition #{comp.id} ({comp.name})"
                            )
        except Exception as e:
            logger.error(f"Error in deadline_reminder_loop: {e}")

    @deadline_reminder_loop.before_loop
    async def before_reminder_loop(self):
        try:
            await self.bot.wait_until_ready()
        except RuntimeError, asyncio.CancelledError:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(CompetitionRadar(bot))
