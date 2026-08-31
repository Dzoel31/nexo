import discord
import logging
from discord import app_commands
from discord.ext import commands
from db.repository import reset_conversation_history
from utils.mcp_client import (
    LLAMA_BASE_URL,
    MCP_SERVER_URL,
    get_tools_from_mcp_server,
)

logger = logging.getLogger("core_commands")


class HelpSelect(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(
                label="Meta & Overview",
                description="General commands, latency, and status",
                emoji="🌟",
                value="0",
            ),
            discord.SelectOption(
                label="AI & LLM Commands",
                description="Slash commands & AI conversation controls",
                emoji="🤖",
                value="1",
            ),
            discord.SelectOption(
                label="IoT & MCP Tools",
                description="Live active tools connected via MCP Server",
                emoji="🧰",
                value="2",
            ),
            discord.SelectOption(
                label="Webhook & Deployment",
                description="GitHub Webhook Gateway & Auto-Deploy",
                emoji="🚀",
                value="3",
            ),
        ]
        super().__init__(
            placeholder="Select a category for more information...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.current_page = int(self.values[0])
        await self.parent_view.update_message(interaction)


class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.author_id = author_id
        self.current_page = 0
        self.total_pages = 4

        self.select_menu = HelpSelect(self)
        self.add_item(self.select_menu)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Help menu ini dibuka oleh pengguna lain. Ketik `$help` untuk membuka menu Anda sendiri!",
                ephemeral=True,
            )
            return False
        return True

    async def fetch_mcp_tools_live(self):
        try:
            mcp_tools = await get_tools_from_mcp_server()
            if mcp_tools:
                self.bot.cached_mcp_tools = mcp_tools
        except Exception as e:
            logger.warning(f"Live MCP retrieval failed during help view: {e}")

    async def build_embed(self) -> discord.Embed:
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(
            name=f"Page {self.current_page + 1}/{self.total_pages}",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None,
        )

        if self.current_page == 0:
            embed.title = "🌟 Meta & General Commands"
            embed.description = (
                "Perintah umum dan informasi status bot Nexo KSM AIoT.\n"
                "─────────────────────────────"
            )
            embed.add_field(
                name="Getting Started",
                value=(
                    "`$help` : Menampilkan panduan pengguna interaktif ini\n"
                    "`$ping` : Cek latensi dan kecepatan respon bot ke Discord\n"
                    "`$status` : Cek status kesehatan llama-server & MCP Server"
                ),
                inline=False,
            )
            embed.add_field(
                name="Management & Moderation",
                value=(
                    "`$clear [limit]` : Hapus pesan percakapan secara masal (Admin)\n"
                    "`$reset [user/all]` : Bersihkan memori percakapan AI"
                ),
                inline=False,
            )

        elif self.current_page == 1:
            embed.title = "🤖 AI & LLM Commands"
            embed.description = (
                "Fitur kecerdasan buatan terintegrasi Llama.cpp & MCP.\n"
                "─────────────────────────────"
            )
            embed.add_field(
                name="Interactive AI Slash Commands",
                value=(
                    "`/tanya [pertanyaan]` : Bertanya ke AI Nexo (Terhubung ke sensor & IoT tools)\n"
                    "`/reset` : Bersihkan riwayat percakapan konteks AI Anda"
                ),
                inline=False,
            )
            embed.add_field(
                name="AI Tools Commands",
                value=(
                    "`$tools` / `/tools` : Tampilkan seluruh tools lokal & MCP aktif\n"
                    "`$reset all` : Bersihkan seluruh memori AI server (Admin)"
                ),
                inline=False,
            )
            embed.add_field(
                name="Fitur Otomatis",
                value="- Menyambut anggota baru di channel *welcome*\n- Menugaskan role otomatis saat perkenalan",
                inline=False,
            )

        elif self.current_page == 2:
            embed.title = "🧰 IoT & MCP Tools (Live Active)"
            embed.description = (
                "Seluruh perkakas (tools) IoT & fungsi eksternal yang dapat diakses AI.\n"
                "─────────────────────────────"
            )
            await self.fetch_mcp_tools_live()

            def _clean_desc(raw_desc: str, max_len: int = 70) -> str:
                if not raw_desc:
                    return "Tidak ada deskripsi."
                first_line = (
                    raw_desc.strip()
                    .split("\n")[0]
                    .split("Args:")[0]
                    .strip()
                    .rstrip(".")
                )
                if len(first_line) > max_len:
                    return first_line[: max_len - 3] + "..."
                return first_line

            # 1. Local Tools
            local_tools = getattr(self.bot, "ai_tools", [])
            if local_tools:
                local_text = "\n".join(
                    [
                        f"• `{t.get('function', {}).get('name', 'Unknown')}` : {_clean_desc(t.get('function', {}).get('description', 'Local Discord tool'))}"
                        for t in local_tools
                    ]
                )
                embed.add_field(
                    name="⚙️ Local Discord Tools", value=local_text, inline=False
                )
            else:
                embed.add_field(
                    name="⚙️ Local Discord Tools",
                    value="*Tidak ada local tool.*",
                    inline=False,
                )

            # 2. Live MCP Tools
            mcp_tools = getattr(self.bot, "cached_mcp_tools", [])
            if mcp_tools:
                mcp_lines = [
                    f"• `{t.get('function', {}).get('name', 'Unknown')}` : {_clean_desc(t.get('function', {}).get('description', 'No description'))}"
                    for t in mcp_tools
                ]
                mcp_text = "\n".join(mcp_lines)
                if len(mcp_text) > 1024:
                    mcp_text = mcp_text[:1020] + "..."
                embed.add_field(
                    name="🌐 Live MCP External Tools (IoT)",
                    value=mcp_text,
                    inline=False,
                )
            else:
                embed.add_field(
                    name="🌐 Live MCP External Tools (IoT)",
                    value="*MCP Server offline atau belum memiliki tools terdaftar.*",
                    inline=False,
                )

        elif self.current_page == 3:
            embed.title = "🚀 Webhook & Auto-Deploy Engine"
            embed.description = (
                "Informasi integrasi GitHub Webhook Gateway & CD Pipeline.\n"
                "─────────────────────────────"
            )
            embed.add_field(
                name="FastAPI Webhook Gateway",
                value=(
                    "• **Endpoint:** `/nexo/webhook`\n"
                    "• **Authentication:** HMAC SHA-256 (`X-Hub-Signature-256`)\n"
                    "• **Routing:** Dikirim otomatis ke Channel Tim sesuai `projects.json`"
                ),
                inline=False,
            )
            embed.add_field(
                name="Continuous Delivery (CD)",
                value=(
                    "• Otomatis me-recreate kontainer Docker VPS saat rilis sukses\n"
                    "• Notifikasi rilis resmi disiarkan ke channel `#release-notes`"
                ),
                inline=False,
            )

        embed.set_footer(
            text="Gunakan dropdown atau tombol di bawah untuk navigasi menu • Nexo KSM AIoT 🚀"
        )
        return embed

    async def update_message(self, interaction: discord.Interaction):
        embed = await self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary, row=1)
    async def first_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page = 0
        await self.update_message(interaction)

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary, row=1)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary, row=1)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
        await self.update_message(interaction)

    @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary, row=1)
    async def last_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.current_page = self.total_pages - 1
        await self.update_message(interaction)

    @discord.ui.button(label="🔄 Refresh MCP", style=discord.ButtonStyle.success, row=1)
    async def refresh_mcp(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        await self.fetch_mcp_tools_live()
        embed = await self.build_embed()
        await interaction.followup.edit_message(
            message_id=interaction.message.id, embed=embed, view=self
        )


class CoreCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Responds with the bot's latency."""
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")

    @commands.command(name="help", aliases=["h", "guide"])
    async def help(self, ctx):
        """Displays the Nexo bot usage guide with interactive UI."""
        view = HelpView(self.bot, ctx.author.id)
        embed = await view.build_embed()
        await ctx.send(embed=embed, view=view)

    @app_commands.command(
        name="help", description="Tampilkan panduan interaktif penggunaan Bot Nexo"
    )
    async def help_slash(self, interaction: discord.Interaction):
        view = HelpView(self.bot, interaction.user.id)
        embed = await view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @commands.command(name="tools", aliases=["mcp", "tool"])
    async def tools(self, ctx):
        """List all available tools with live MCP retrieval."""
        view = HelpView(self.bot, ctx.author.id)
        view.current_page = 2  # Jump to MCP Tools page directly
        embed = await view.build_embed()
        await ctx.send(embed=embed, view=view)

    @app_commands.command(
        name="tools", description="Tampilkan seluruh tools lokal & MCP aktif saat ini"
    )
    async def tools_slash(self, interaction: discord.Interaction):
        view = HelpView(self.bot, interaction.user.id)
        view.current_page = 2
        embed = await view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @commands.command()
    async def status(self, ctx):
        """Check the status of services."""
        status_messages = ["🔍 Checking service status..."]

        import aiohttp

        # Check llama-server
        logger.info(f"Server llama.cpp: {LLAMA_BASE_URL.replace('/v1', '')}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{LLAMA_BASE_URL.replace('/v1', '')}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        status_messages.append("✅ llama-server: ONLINE")
                    else:
                        status_messages.append("⚠️ llama-server: RESPONDING (non-200)")
        except Exception:
            status_messages.append("❌ llama-server: OFFLINE")

        # Check MCP server
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{MCP_SERVER_URL}/", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        status_messages.append("✅ MCP Server: ONLINE")
                    else:
                        status_messages.append("⚠️ MCP Server: RESPONDING (non-200)")
        except Exception:
            status_messages.append("❌ MCP Server: OFFLINE")

        await ctx.send("\n".join(status_messages))

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        """Syncs slash commands to the current guild."""
        await ctx.send("🔄 Syncing commands...")
        self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ Successfully synced slash commands in this server!")

    @commands.command()
    async def clear(self, ctx, limit: int = 100):
        """Deletes messages in bulk or one by one with a delay."""
        if not ctx.author.guild_permissions.manage_messages:
            return await ctx.send("❌ You do not have Manage Messages permission.")

        await ctx.send(f"🧹 Starting deletion of {limit} messages...")

        try:
            # channel.purge() automatically handles bulk_delete (<14 days) and single delete (>14 days)
            deleted = await ctx.channel.purge(limit=limit + 2)
            await ctx.send(
                f"✅ Successfully deleted {len(deleted)} messages!", delete_after=5
            )
        except discord.Forbidden:
            await ctx.send("❌ Bot does not have Manage Messages permission.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ HTTP Error occurred: {e}")

    @commands.command(aliases=["resetcontext", "clearcontext"])
    async def reset(self, ctx, mode: str = "user"):
        """Resets the AI conversation history and memory context."""
        if mode.lower() == "all":
            if not ctx.author.guild_permissions.manage_messages:
                return await ctx.send(
                    "❌ You need 'Manage Messages' permission to reset all conversation context."
                )
            if hasattr(self.bot, "conversation_history"):
                self.bot.conversation_history.clear()
            msg = "Global AI conversation memory context has been cleared for all users! 🧹✨"
        else:
            await reset_conversation_history(ctx.author.id)
            if hasattr(self.bot, "conversation_history"):
                self.bot.conversation_history.pop(ctx.author.id, None)
            msg = f"AI conversation memory context cleared for <@{ctx.author.id}>! 🧹✨"

        embed = discord.Embed(
            title="🧠 Context Reset",
            description=msg,
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @app_commands.command(
        name="reset", description="Clear your AI conversation context memory"
    )
    async def reset_slash(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        await reset_conversation_history(user_id)
        if hasattr(self.bot, "conversation_history"):
            self.bot.conversation_history.pop(user_id, None)

        embed = discord.Embed(
            title="🧠 Context Reset",
            description=f"AI conversation memory context cleared for <@{user_id}>! 🧹✨",
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed)

    @commands.command(name="voice", aliases=["vc", "voicechannel"])
    async def voice_cmd(self, ctx, *, channel_name: str = None):
        """Get list of users currently in a voice channel."""
        target_vc = None

        if channel_name and channel_name.strip():
            c_name = channel_name.lower().strip()
            for vc in ctx.guild.voice_channels:
                if c_name in vc.name.lower():
                    target_vc = vc
                    break

        if not target_vc and isinstance(
            ctx.channel, (discord.VoiceChannel, discord.StageChannel)
        ):
            target_vc = ctx.channel

        if not target_vc and ctx.author.voice and ctx.author.voice.channel:
            target_vc = ctx.author.voice.channel

        if not target_vc:
            if channel_name:
                return await ctx.send(
                    f"Voice Channel containing '{channel_name}' was not found."
                )
            return await ctx.send(
                "Please specify a voice channel name, join a voice channel, or run this command inside a voice channel text chat."
            )

        members = target_vc.members
        embed = discord.Embed(
            title=f"🔊 Voice Channel: {target_vc.name}",
            color=discord.Color.blue(),
        )

        if not members:
            embed.description = "Currently, there is no one in this Voice Channel."
        else:
            member_list = [f"• {m.mention} ({m.display_name})" for m in members]
            embed.description = f"**Total Members:** {len(members)}\n\n" + "\n".join(
                member_list
            )

        embed.set_footer(text=f"Server: {ctx.guild.name} • Nexo KSM AIoT")
        await ctx.send(embed=embed)

    @app_commands.command(
        name="voice", description="Check current members in a voice channel"
    )
    @app_commands.describe(channel_name="Name of the voice channel to check (optional)")
    async def voice_slash(
        self, interaction: discord.Interaction, channel_name: str = None
    ):
        target_vc = None

        if channel_name and channel_name.strip():
            c_name = channel_name.lower().strip()
            for vc in interaction.guild.voice_channels:
                if c_name in vc.name.lower():
                    target_vc = vc
                    break

        if not target_vc and isinstance(
            interaction.channel, (discord.VoiceChannel, discord.StageChannel)
        ):
            target_vc = interaction.channel

        if not target_vc and interaction.user.voice and interaction.user.voice.channel:
            target_vc = interaction.user.voice.channel

        if not target_vc:
            if channel_name:
                return await interaction.response.send_message(
                    f"Voice Channel containing '{channel_name}' was not found."
                )
            return await interaction.response.send_message(
                "Please specify a voice channel name, join a voice channel, or run this command inside a voice channel text chat."
            )

        members = target_vc.members
        embed = discord.Embed(
            title=f"🔊 Voice Channel: {target_vc.name}",
            color=discord.Color.blue(),
        )

        if not members:
            embed.description = "Currently, there is no one in this Voice Channel."
        else:
            member_list = [f"• {m.mention} ({m.display_name})" for m in members]
            embed.description = f"**Total Members:** {len(members)}\n\n" + "\n".join(
                member_list
            )

        embed.set_footer(text=f"Server: {interaction.guild.name} • Nexo KSM AIoT")
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(CoreCommands(bot))
