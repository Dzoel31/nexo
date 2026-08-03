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
intents.members = True  # Required for on_member_join events

bot = commands.Bot(command_prefix="$", intents=intents, help_command=None)

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

    # Load all local Cogs
    cogs_to_load = [
        "cogs.core_commands",
        "cogs.agent_orchestrator",
        "cogs.server_events",
    ]

    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded {cog} successfully")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")

    await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually (KeyboardInterrupt).")
