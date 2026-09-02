# Nexo 🤖

**Nexo** adalah asisten Discord cerdas bertenaga LLM (*Large Language Model*) lokal dan *Model Context Protocol* (MCP) yang dikembangkan khusus untuk **KSM AIoT** (Kelompok Studi Mahasiswa Artificial Intelligence & Internet of Things, UPN "Veteran" Jakarta).

Nexo bertindak sebagai *Smart Community Assistant* yang mampu berinteraksi secara kontekstual, mengelola acara komunitas, menyinkronkan jadwal dengan Google Calendar, memproses Webhook GitHub CI/CD, hingga memicu *redeploy* kontainer otomatis via Portainer Webhook API dengan otorisasi keamanan berbasis peran (RBAC).

---

## 🏛️ Arsitektur Sistem

Berikut adalah gambaran arsitektur sistem Nexo:

```mermaid
flowchart TB
    subgraph Discord_Ecosystem["Discord Ecosystem"]
        User["Discord User / Admin"]
        Guild["Discord Server (KSM AIoT)"]
    end

    subgraph Nexo_Core["Nexo Bot Core (discord.py + asyncio)"]
        Orchestrator["Agent Orchestrator\n(Task Queue, Cooldown, Context Memory)"]
        AuthHelper["Auth Helper\n(RBAC & config/roles.json)"]
        ServerEvents["Server Events & Lifecycle\n(Event Manager, Reminders Task)"]
        WebhookDeploy["Webhook & Deploy Cog\n(Portainer Integration)"]
        FastAPIGateway["FastAPI Gateway Server\n(/nexo/webhook)"]
    end

    subgraph AI_Infrastructure["AI & External Services"]
        LLM["Llama.cpp Engine\n(Gemma 4 E2B GGUF)"]
        MCP["MCP Server\n(Tools & Knowledge Base)"]
        GCal["Google Calendar API\n(Service Account)"]
        Portainer["Portainer Webhook API\n(Container Auto-Redeploy)"]
    end

    subgraph Database_Layer["Database Layer"]
        Postgres[(PostgreSQL\nAsyncpg + SQLAlchemy)]
        Alembic["Alembic Migrations"]
    end

    User <-->|Slash Command / Mention| Guild
    Guild <--> Nexo_Core
    FastAPIGateway <---|GitHub Webhooks| GitHub["GitHub Actions / Repositories"]
    
    Orchestrator -->|Authorization Check| AuthHelper
    Orchestrator <-->|Inference & Tools| LLM
    Orchestrator <-->|External Tools| MCP
    
    ServerEvents <-->|Sync Events| GCal
    ServerEvents <-->|State Persistence| Postgres
    
    WebhookDeploy -->|Trigger HTTP POST| Portainer
```

---

## ✨ Fitur Utama

- **Conversational AI & Group Context:** Nexo dapat ditanya melalui mention `@Nexo` di channel mana pun atau melalui slash command `/tanya`. Nexo secara cerdas membaca percakapan sebelumnya untuk mempertahankan konteks dialog.
- **Asynchronous Task Queue & Rate Limiting:** Menggunakan antrean *non-blocking* dengan sliding cooldown 5 detik per pengguna guna mencegah *queue starvation* atau serangan Denial of Service (DoS).
- **Local AI Tools & Strict Pydantic Schemas:** LLM dapat memanggil fungsi-fungsi lokal Discord menggunakan skema validasi Pydantic yang ketat:
  - 📅 **Manajemen Acara:** Membuat dan mengakhiri Discord Scheduled Events lengkap dengan siaran pengumuman dinamis.
  - 📆 **Sinkronisasi Google Calendar:** Integrasi dua arah dengan Google Calendar menggunakan Google Service Account.
  - ⏰ **Smart Event Reminders:** Background task yang otomatis mengirimkan pengingat H-7, H-3, H-1, H-3 jam, H-1 jam, dan saat acara dimulai dengan format bahasa Indonesia (WIB).
  - 🧵 **Thread Creation & Polls:** Membuat forum diskusi thread dan jajak pendapat interaktif.
  - 🧹 **Message Purge:** Membersihkan pesan di channel secara aman dan asinkron.
- **Role-Based Access Control (RBAC):** Seluruh aksi destruktif atau administratif diverifikasi melalui `utils/auth_helper.py` menggunakan `config/roles.json` dan Discord `guild_permissions`.
- **CI/CD Gateway & Portainer Auto-Deploy:** Menerima payload webhook dari GitHub (`push`, `pull_request`, `workflow_run`) dan memicu pembaruan kontainer via Portainer Webhook API secara terisolasi tanpa *Docker socket exposure*.
- **Token Analytics & Tracking:** Menghitung penggunaan token prompt dan response secara akurat dengan endpoint tokenisasi lokal, serta menyediakan command `/token-stats`.

---

## 📂 Struktur Folder & Proyek

```
nexo/
├── .agents/                    # Aturan agen AI & konvensi proyek
├── config/
│   ├── projects.json           # Pemetaan repo GitHub ke channel Discord & webhook Portainer
│   └── roles.json              # Pemetaan nama role server ke ID Snowflake Discord
├── cogs/                       # Modular Discord Cogs (Fitur Bot)
│   ├── agent_orchestrator.py   # Antrean AI, rate limiting, context memory, /tanya
│   ├── core_commands.py        # Command utilitas dasar ($ping, $clear)
│   ├── help_command.py         # Menu bantuan interaktif
│   ├── server_events.py        # Handler AI tool Discord, reminder loop, sinkronisasi GCal
│   └── webhook_deploy.py       # Dispatcher notifikasi webhook & trigger Portainer
├── db/                         # Layer Database
│   ├── models.py               # Definisi model SQLAlchemy (ScheduledEvent, TokenLog, dll.)
│   ├── repository.py           # Operasi database & query parameterized
│   └── session.py              # Konfigurasi async engine & sessionmaker (asyncpg)
├── migrations/                 # Migrasi database Alembic
│   ├── env.py
│   └── versions/               # Script revisi migrasi skema tabel
├── prompts/
│   └── system_prompt.md        # Prompt sistem dasar, persona, dan aturan Nexo
├── templates/                  # Jinja2 Templates
│   ├── events/                 # Template broadcast & pengingat acara (Indonesian WIB)
│   └── webhooks/               # Template notifikasi GitHub Actions & commits
├── tests/                      # Suite pengujian unit & integrasi (Pytest)
│   ├── test_auth_helper.py
│   ├── test_dynamic_event_messages.py
│   ├── test_event_manager_and_templates.py
│   ├── test_reminder_system.py
│   ├── test_server_events_tools.py
│   ├── test_token_cache_and_analytics.py
│   ├── test_tool_execution.py
│   └── test_webhook_templates.py
├── utils/                      # Modul Utilitas & Helper
│   ├── auth_helper.py          # Otorisasi RBAC terpusat & permission check
│   ├── event_manager.py        # Logic pengingat, timezone WIB, pruning interval
│   ├── gateway_server.py       # FastAPI server untuk menangani webhook GitHub
│   ├── gcal_manager.py         # Klien Google Calendar API
│   ├── mcp_client.py           # Klien LLM OpenAI-compatible & eksekutor tool MCP
│   ├── schemas.py              # Pydantic models untuk AI tool calling
│   └── template_renderer.py    # Engine rendering template Jinja2
├── docker-compose.yml          # Konfigurasi kontainer Docker Nexo
├── pyproject.toml              # Definisi dependensi & metadata proyek (uv)
└── uv.lock                     # Lockfile dependensi deterministik
```

---

## ⚙️ Konfigurasi Environment Variables (`.env`)

Buat file `.env` di root direktori dengan konfigurasi berikut:

```env
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
PORT=8000
HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nexo_db

# LLM & MCP Engine
LLAMA_SERVER_URL=http://localhost:8080/v1
LLAMA_TOKENIZE_URL=http://localhost:8080/tokenize
MCP_SERVER_URL=http://localhost:8001/sse

# Google Calendar Integration (Opsional)
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com

# GitHub Webhook & Channels
GITHUB_SECRET=your_github_webhook_secret
ANNOUNCEMENT_CHANNEL_ID=123456789012345678
WEBHOOK_DEVLOGS_CHANNEL_ID=123456789012345678
WEBHOOK_RELEASE_NOTES_CHANNEL_ID=123456789012345678
WELCOME_AND_RULES_CHANNEL_ID=123456789012345678
```

---

## 🚀 Panduan Menjalankan

### 1. Prasyarat
- **Python 3.14+**
- **[uv](https://github.com/astral-sh/uv)** (Manajer paket Python)
- **PostgreSQL Database**

### 2. Instalasi Dependensi
```bash
uv sync
```

### 3. Migrasi Database (Alembic)
Jalankan migrasi skema database terbaru:
```bash
uv run alembic upgrade head
```

### 4. Menjalankan Bot
```bash
uv run main.py
```

---

## 🧪 Pengujian & Standar Kualitas Kode

Proyek ini menerapkan standar linting yang ketat menggunakan `ruff` dan pengujian otomatis dengan `pytest`.

### Menjalankan Linter & Formatter
```bash
uv run ruff check --fix .
uv run ruff format .
```

### Menjalankan Unit Tests
```bash
uv run pytest
```

---

## 🔒 Keamanan & Praktik Terbaik
1. **No Docker Socket Mounting:** Bot berjalan dalam *least-privilege mode* tanpa mount `/var/run/docker.sock`. Semua tindakan *deployment* didelegasikan ke webhook terautentikasi Portainer.
2. **Sanitized Error Outputs:** Kesalahan runtime internal tidak dibocorkan ke pengguna publik guna mencegah *information disclosure*.
3. **Strict Parameterized Queries:** Seluruh interaksi database menggunakan ORM SQLAlchemy dan query berparameter untuk mencegah SQL Injection.
4. **Token Security:** Kredensial dan token disimpan murni di variabel lingkungan (*environment variables*).