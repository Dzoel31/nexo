import os
import json
import logging
from datetime import datetime
import traceback
import aiohttp
import discord
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI

logger = logging.getLogger("mcp_client")

# ---------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------------------------------------
LLAMA_SERVER_URL = os.environ.get(
    "LLAMA_SERVER_URL", "http://localhost:8080/v1/chat/completions"
)
LLAMA_BASE_URL = LLAMA_SERVER_URL.replace("/chat/completions", "")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000")
MAX_HISTORY_TURNS = 5

# Load System Prompt
try:
    with open("prompts/system_prompt.md", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "You are Nexo, a helpful assistant."
    logger.warning("prompts/system_prompt.md not found. Using default prompt.")

ai_client = AsyncOpenAI(base_url=LLAMA_BASE_URL, api_key="sk-no-key")


async def get_tools_from_mcp_server() -> list:
    # Try a couple of likely endpoints so this client is resilient to
    # whether the streamable MCP app is mounted at `/` or `/mcp`.
    candidates = [MCP_SERVER_URL.rstrip("/") + "/sse"]

    def _get_field(obj, key):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    last_exc = None
    for url in candidates:
        try:
            async with sse_client(url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools_response = await session.list_tools()

                    llm_tools = []
                    for tool in getattr(tools_response, "tools", []) or []:
                        name = _get_field(tool, "name")
                        desc = _get_field(tool, "description") or ""

                        # input schema may be provided under different names or as a string
                        raw_schema = (
                            _get_field(tool, "inputSchema")
                            or _get_field(tool, "input_schema")
                            or _get_field(tool, "parameters")
                            or _get_field(tool, "schema")
                        )

                        parameters = None
                        if raw_schema:
                            if isinstance(raw_schema, str):
                                try:
                                    parameters = json.loads(raw_schema)
                                except Exception:
                                    parameters = None
                            elif isinstance(raw_schema, dict):
                                parameters = raw_schema

                        if not parameters:
                            parameters = {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": True,
                            }

                        if name:
                            llm_tools.append(
                                {
                                    "type": "function",
                                    "function": {
                                        "name": name,
                                        "description": desc,
                                        "parameters": parameters,
                                    },
                                }
                            )

                    return llm_tools
        except Exception as e:
            last_exc = e
            continue

    # If we couldn't connect to any candidate URL, raise a clear error.
    raise RuntimeError(f"Unable to fetch tools from MCP server: {last_exc}")


async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute an MCP tool by calling the actual MCP server.
    """
    candidates = [MCP_SERVER_URL.rstrip("/") + "/sse"]
    for url in candidates:
        try:
            async with sse_client(url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

                    if hasattr(result, "content") and isinstance(result.content, list):
                        text_results = []
                        for content in result.content:
                            if content.type == "text":
                                text_results.append(content.text)

                        combined = "\n".join(text_results)
                        return combined
                    else:
                        return str(result)
        except Exception as e:
            error_msg = f"Error calling MCP tool '{tool_name}' at {url}: {str(e)}"
            logger.error(error_msg)
            continue

    return "⚠️ Tool execution failed or unable to connect."


async def check_services_health():
    """Returns True if both services are up, False and an error message otherwise."""
    try:
        async with aiohttp.ClientSession() as session:
            # Check llama-server
            try:
                async with session.get(
                    f"{LLAMA_BASE_URL.replace('/v1', '')}/health",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as response:
                    if response.status != 200:
                        return (
                            False,
                            "⚠️ **llama-server** responded with an error (non-200).",
                        )
            except Exception:
                return (
                    False,
                    "❌ **llama-server** is OFFLINE. Please start the LLM server.",
                )

            # Check MCP server
            try:
                async with session.get(
                    f"{MCP_SERVER_URL}/", timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status != 200:
                        return (
                            False,
                            "⚠️ **MCP Server** responded with an error (non-200).",
                        )
            except Exception:
                return (
                    False,
                    "❌ **MCP Server** is OFFLINE. Please start the MCP server.",
                )

    except Exception as e:
        return False, f"An error occurred while checking servers: {str(e)}"

    return True, "All systems go"


async def process_with_mcp_tools(
    bot,
    user_id: int,
    user_name: str,
    user_question: str,
    max_iterations: int = 3,
    ctx_obj=None,
):
    """
    Process a user question with MCP tool support and context memory.
    Returns (reply_text, used_tools_boolean)
    """
    if user_id not in bot.conversation_history:
        bot.conversation_history[user_id] = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    messages.extend(bot.conversation_history.get(user_id, []))

    current_time_str = datetime.now().strftime("%A, %d %B %Y - %H:%M WIB")

    # Extract Channel & Voice Channel info from ctx_obj
    channel_name = "Unknown"
    is_voice_chat = False
    user_vc_name = "None"

    if ctx_obj and hasattr(ctx_obj, "channel") and ctx_obj.channel:
        channel_name = getattr(ctx_obj.channel, "name", "Unknown")
        is_voice_chat = isinstance(
            ctx_obj.channel, (discord.VoiceChannel, discord.StageChannel)
        )

    user_obj = getattr(ctx_obj, "author", getattr(ctx_obj, "user", None))
    if (
        user_obj
        and hasattr(user_obj, "voice")
        and user_obj.voice
        and user_obj.voice.channel
    ):
        user_vc_name = user_obj.voice.channel.name

    dynamic_user_prompt = (
        f"<system_context>\n"
        f"Current Time WIB: {current_time_str}\n"
        f"User: {user_name} (<@{user_id}>)\n"
        f"Current Channel: #{channel_name} (Is Voice Chat: {is_voice_chat})\n"
        f"User Connected Voice Channel: {user_vc_name}\n"
        f"</system_context>\n"
        f"{user_question}"
    )

    messages.append({"role": "user", "content": dynamic_user_prompt})

    used_tools = False

    for iteration in range(max_iterations):
        # Combine tools from local Cogs and external MCP
        all_tools = []
        if getattr(bot, "ai_tools", None):
            all_tools.extend(bot.ai_tools)
        if getattr(bot, "cached_mcp_tools", None):
            all_tools.extend(bot.cached_mcp_tools)

        kwargs = {
            "model": "local-model",
            "messages": messages,
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
        }
        if all_tools:
            kwargs["tools"] = all_tools

        try:
            response = await ai_client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            message = choice.message

            # Check if the model wants to call a tool
            if message.tool_calls:
                used_tools = True
                # Add the assistant's message to the conversation
                messages.append(message)

                # Execute all tool calls
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name

                    # Parse arguments - handle both string and dict formats
                    args = tool_call.function.arguments
                    if isinstance(args, str):
                        arguments = json.loads(args)
                    else:
                        arguments = args

                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    # Execute tool: Check if it's a Local Tool from a Cog, if not, send to MCP Server
                    if (
                        hasattr(bot, "local_tool_handlers")
                        and tool_name in bot.local_tool_handlers
                    ):
                        import inspect

                        handler = bot.local_tool_handlers[tool_name]
                        sig = inspect.signature(handler)
                        if "ctx_obj" in sig.parameters:
                            result = await handler(arguments, ctx_obj=ctx_obj)
                        else:
                            result = await handler(arguments)
                    else:
                        result = await execute_mcp_tool(tool_name, arguments)

                    # Add the tool result to the conversation
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": result,
                        }
                    )
                    # Format log for better readability (especially for large JSON structures)
                    try:
                        parsed = json.loads(result)
                        if isinstance(parsed, list):
                            log_msg = f"[Retrieved {len(parsed)} data items]"
                        elif isinstance(parsed, dict):
                            log_msg = f"[Retrieved JSON object with {len(parsed.keys())} keys]"
                        else:
                            log_msg = str(result)[:100] + (
                                "..." if len(str(result)) > 100 else ""
                            )
                    except json.JSONDecodeError, TypeError:
                        log_msg = str(result)[:100] + (
                            "..." if len(str(result)) > 100 else ""
                        )

                    logger.info(f"Tool '{tool_name}' result: {log_msg}")

                # Continue to next iteration to let the model process the results
                continue
            else:
                # No tool calls, return the final response
                reply = message.content or "I don't have a response."

                # Update conversation history cleanly
                bot.conversation_history[user_id].append(
                    {"role": "user", "content": user_question}
                )
                bot.conversation_history[user_id].append(
                    {"role": "assistant", "content": reply}
                )

                if len(bot.conversation_history[user_id]) > MAX_HISTORY_TURNS * 2:
                    bot.conversation_history[user_id] = bot.conversation_history[
                        user_id
                    ][-MAX_HISTORY_TURNS * 2 :]

                return reply, used_tools

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            traceback.print_exc()
            return f"I encountered an error: {str(e)}", False

    return (
        "I've tried using tools but couldn't complete your request. Please try again or rephrase your question.",
        used_tools,
    )
