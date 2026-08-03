# Nexo 🤖

**Nexo** is an intelligent, LLM-powered Discord Assistant Bot developed for **KSM AIoT** (Kelompok Studi Mahasiswa Artificial Intelligence & Internet of Things). 

Nexo acts as a smart community assistant, capable of answering questions, engaging in contextual conversations, and executing various community management tools natively within Discord.

## ✨ Features

- **Conversational AI**: Tag `@Nexo` in any channel or use the `/tanya` slash command to ask questions. When tagged, Nexo reads up to 10 previous messages to maintain conversational context.
- **Smart Orchestration**: Uses a built-in `AgentOrchestrator` with an asynchronous queue system to handle multiple user queries gracefully without overloading the LLM server.
- **MCP Integration**: Connects to external Model Context Protocol (MCP) servers to fetch real-time data and leverage external APIs.
- **Local Discord Tools**: The AI can dynamically execute Discord actions via strict Pydantic schemas, such as:
  - 🗑️ Purging/clearing messages dynamically
  - 🧵 Creating threads
  - 📅 Scheduling Discord Events
  - 📊 Creating Polls
- **Health Checks**: Built-in heartbeat checks for both the local LLM server and the MCP server before processing heavy tasks.

## 🛠️ Tech Stack

- **Python**: Core logic.
- **discord.py**: Discord API wrapper.
- **uv**: Lightning-fast Python package installer and resolver.
- **ruff**: An extremely fast Python linter and code formatter.
- **llama.cpp**: The local LLM engine powering Nexo's brain.
- **Pydantic**: Used for strict schema definitions in tool execution.

## 🚀 Getting Started

### Prerequisites

1. Install **Python 3.10+**.
2. Install **[uv](https://github.com/astral-sh/uv)** for dependency management.
3. You need a running instance of `llama.cpp` (LLM server) and your custom MCP server.

### Installation

1. Clone this repository.
2. Create a `.env` file in the root directory and add your Discord Bot Token:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   ```
3. Run the bot using `uv`:
   ```bash
   uv run main.py
   ```

## 📂 Project Structure

- `main.py`: Entry point for the Discord bot.
- `cogs/`: Contains the modular bot extensions.
  - `agent_orchestrator.py`: Manages the async queue and LLM task processing.
  - `core_commands.py`: Basic bot commands (e.g., ping, clear).
  - `server_events.py`: Discord event listeners and local AI tool handlers.
- `utils/`: Helper modules.
  - `mcp_client.py`: The bridge between the bot, the LLM server, and the MCP server.
  - `schemas.py`: Pydantic models for structured tool arguments.
- `prompts/`: Contains `system_prompt.md` which dictates Nexo's personality and rules.

## 🧹 Code Quality

This project strictly adheres to `ruff` for linting and formatting. 
Before submitting any changes, ensure you run:
```bash
uv run ruff check --fix .
uv run ruff format .
```