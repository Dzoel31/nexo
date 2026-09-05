import os
import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

load_dotenv()
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
default_mentions = discord.AllowedMentions(
    everyone=False,
    roles=False,
    users=True,
    replied_user=True,
)

bot = commands.Bot(
    command_prefix="$",
    intents=intents,
    help_command=None,
    allowed_mentions=default_mentions,
)

# Bot Variables (Global State)
bot.ai_tools = []
bot.local_tool_handlers = {}
bot.conversation_history = {}
bot.cached_mcp_tools = []


@bot.event
async def on_ready():
    # Set Custom Presence (Bot Status)
    await bot.change_presence(
        activity=discord.Game(name="Guiding You to the Future 🚀 | $help")
    )
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

    # Sync application slash commands to Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} application slash commands globally.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    logger.info("------")


@bot.event
async def on_message(message):
    # Prevents the bot from replying to itself
    if message.author == bot.user:
        return
    # CRUCIAL: This line is needed for prefix commands to work
    await bot.process_commands(message)


async def main():
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set.")
        return

    from db.repository import close_http_session

    try:
        # Load all local Cogs
        cogs_to_load = [
            "cogs.core_commands",
            "cogs.agent_orchestrator",
            "cogs.server_events",
            "cogs.webhook_deploy",
            "cogs.competition_radar",
        ]

        for cog in cogs_to_load:
            try:
                await bot.load_extension(cog)
                logger.info(f"Loaded {cog} successfully")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        # Launch FastAPI Webhook Gateway Server in background task
        from utils.gateway_server import start_gateway_server

        asyncio.create_task(start_gateway_server(bot))

        await bot.start(TOKEN)
    finally:
        await close_http_session()
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually (KeyboardInterrupt).")
