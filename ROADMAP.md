# 🚀 Peta Jalan & Fitur (Roadmap) KSM AIoT Bot

Dokumen ini adalah gabungan cetak biru (blueprint) arsitektur, fase pengembangan, rencana DevOps, daftar tugas, dan ide fitur untuk Nexo Bot KSM AIoT.

---

## 1. Komparasi Arsitektur (Current vs Future State)

Berikut adalah perbandingan fungsionalitas bot saat ini dengan rencana arsitektur berstandar *Enterprise/DevOps*:

| Layer / Komponen | 🔴 Kondisi Saat Ini (Current State) | 🟢 Rencana Kedepan (Future State) |
| :--- | :--- | :--- |
| **1. Ingress Layer** | Hanya merespons dari interaksi chat Discord via WebSocket (`discord.py`). | Merespons Discord **ditambah** endpoint khusus HTTP Webhook eksternal (GitHub Actions & Sensor). |
| **2. Bot Gateway** | Belum ada web server mumpuni. | Menggunakan **FastAPI** dengan perlindungan *HMAC Webhook Signature*, *Deduplication*, dan *Guardrails*. |
| **3. Agent Orchestrator** | - *Memory chat* in-memory (hilang jika *restart*).<br>- Semua tools dikirim ke LLM sekaligus. | - *Memory Manager* terhubung ke Database.<br>- **Dynamic Tool Router** dengan Vector Search (`pgvector`). |
| **4. Inference Engine** | `llama-server` (AsyncOpenAI) + Gemma 4 E2B. | Sistem pencegahan error yang memvalidasi *context length* maksimal **8,192 token**. |
| **5. Tool Executor** | Eksekusi via `json.loads` sederhana. | Validasi ketat menggunakan **Pydantic**. |
| **6. Persistence (DB)** | **Tidak ada database.** | Menggunakan **PostgreSQL + pgvector** untuk riwayat, sistem RAG, dan *Audit Logging*. |

---

## 2. Fase Pengembangan Utama

Berdasarkan pertimbangan perangkat keras (4 Core CPU, sisa RAM 5 GB), pengembangan dibagi menjadi 3 fase:

### 🟢 Fase 1: Inti (Core Bot & MCP Integration) - *Hampir Rampung*
- Integrasi `llama-server` (Gemma) dengan antarmuka Discord.
- MCP Integration untuk membaca skema sensor hidroponik secara langsung (*Direct Injection*).
- Pydantic Validation (Dasar).

### 🟡 Fase 2: Gateway, WebHooks & Auto-Deploy (Pigeon Style) - *Persiapan*
- **FastAPI WebHook Gateway:** Menerima *payload* dari GitHub dengan perlindungan otentikasi HMAC.
- **Pydantic & Jinja Templating:** Memvalidasi struktur JSON Webhook secara ketat dengan Pydantic, lalu merender notifikasi yang rapi menggunakan Jinja Template sebelum dikirim ke Discord.
- **Auto-Deploy Engine:** Eksekusi otomatis sintaks deployment (contoh: `docker compose pull && docker compose up -d`) pada *path* proyek yang sesuai ketika ada rilis atau *push* dari GitHub.
- **Observability API:** Endpoint terpisah untuk memantau status sistem dan kesehatan bot dari *Web Dashboard*.

### 🔴 Fase 3: Skalabilitas Vektor - *Ditunda (Sampai Tools Melebihi Batas Context Window)*
- PostgreSQL Database & Vector DB (`pgvector`).
- Tool Router Berbasis RAG (menyaring tools dengan BGE-small sebelum dikirim ke LLM).

---

## 3. Rencana DevOps & Observability

### Fase 1: Smart CI/CD
- **Hybrid Approach:** GitHub Actions mem-build image -> SSH ke VPS -> Eksekusi `docker compose pull && up`.
- **Smart Error Catching:** Jika deploy gagal, log stderr dilempar via webhook ke Discord. LLM (Gemma 4 E2B) akan menerjemahkan log error tersebut menjadi pesan teknis yang mudah dipahami.

### Fase 2: Web Dashboard (Observability)
- **Pemisahan:** Web Dashboard bertindak untuk *Observability* (Melihat antrean, health check, log), sedangkan Discord untuk *Operability* (Eksekusi /Tanya bot).
- Mini web-server berjalan berdampingan dengan `discord.py` di *background task* menggunakan `asyncio`.

### Fase 3: KSM AIoT Dashboard Center
- **Trigger Eksternal:** Aksi di Web (misal: membagi tugas rapat di kalender) men-trigger API internal bot.
- Bot Discord akan memproses data JSON lewat LLM agar kalimatnya ramah dan tidak kaku, lalu mengirimkannya sebagai *Direct Message* (DM) ke anggota KSM yang ditugaskan.

---

## 4. Ide Fitur Bot (Dioptimasi untuk *Context Window*)

> ⚠️ **PERHATIAN: BATASAN CONTEXT WINDOW (Dibatasi 8,192 Tokens)**
> Model **Gemma 4 E2B (GGUF Q4_K_M)** yang digunakan sebenarnya memiliki kapasitas token yang besar (bisa di-*push* hingga 16K token di *environment* ini), namun **sengaja dibatasi maksimal 8K token** (gabungan *system prompt*, *chat history*, skema *tools*, dan *output*) agar tidak memicu *Out of Memory* (OOM) pada RAM server (5GB). Oleh karena itu, fitur-fitur di bawah ini **wajib dirancang dengan efisien**.

### A. Summarizer & AI Assistant
- **Chat Summarizer (Bertingkat/Paginated):** Bot **dilarang keras** menarik 500 chat sekaligus. Bot hanya mengambil 20-30 pesan terakhir per eksekusi, atau merangkum secara parsial lalu digabung (Rangkuman dari Rangkuman).
- **Research Assistant (Jurnal/Artikel PDF):** Bot tidak bisa membaca 1 PDF utuh di *context window*. Wajib menggunakan RAG (*Retrieval-Augmented Generation*). PDF dipecah (*chunking*), lalu saat user bertanya, bot men-search vektor untuk menarik 3-4 paragraf yang relevan saja.
- **Notulensi Pintar:** Menerima *pointer* ringkas dari pengurus di akhir rapat, lalu merapikannya menjadi format notula (Keputusan & Action Items).

### B. Komunitas & Produktivitas
- **Pengingat Rapat & Kalender:** *Blast* notifikasi rapat (bisa statis tanpa LLM agar hemat *context window*).
- **Absensi/Presensi Digital (Voice Channel):** Fitur presensi cerdas di mana bot tidak perlu ikut masuk dan *stay* di Voice Channel (VC). Cukup panggil `/hadir_vc`, lalu bot akan membaca API Discord untuk mendata siapa saja *member* yang sedang *nongkrong* di VC tersebut dan langsung mencatatnya ke Database.
- **Gamifikasi & Poin Keaktifan:** Penghitungan poin (Leaderboard) dari frekuensi menjawab di *help channel* atau dari kontribusi/komit di GitHub.
- **Sistem Onboarding:** Sambutan anggota baru otomatis via DM/Channel.

### C. Alat Bantu Riset & Lab
- **Inventaris Lab IoT:** Cek ketersediaan sensor (ESP32, DHT22) langsung ke database.
- **Live Sensor Monitoring:** Slash command untuk menarik cuplikan ringkas (*snapshot*) data *real-time* kelembaban/suhu lab IoT.
- **Code Assistant Terarah:** Menjawab *error code* spesifik mikrokontroler. *Chat history* akan otomatis dipangkas (*rolling window*) jika menyentuh 6,000 token agar sisa ruang cukup untuk menampung jawaban.
- **Learning Assistant (RAG Engine):** Memasukkan kumpulan *datasheet* komponen (ESP32, IC, sensor) dan kumpulan materi dari KSM AIoT sendiri, serta bisa dari sumber eksternal (web search). Anggota KSM dapat bertanya ke bot dan mendapatkan jawaban beserta referensinya.
- **Eksekusi Fisik / Hardware-in-the-Loop (Target Masa Depan):** Bot diberi kapabilitas mengeksekusi *actuator* di lab fisik, seperti me-restart node server atau menghidupkan *relay* MQTT langsung lewat command Discord.

### D. Utilitas Server & Manajemen Proyek
- **Polling Dinamis:** Memfasilitasi musyawarah atau penentuan jadwal lewat sistem *voting* yang rapi dan bisa dibatasi khusus *role* tertentu.
- **Ruang Proyek Sementara (Discord Threads):** Daripada membuat *Text Channel* baru yang membuat server berantakan, anggota bisa *request* pembuatan **Discord Thread** khusus tim lomba/proyek. Kelebihannya, *Thread* akan **otomatis diarsipkan (auto-archive)** oleh Discord sendiri jika tidak ada yang *chat* lagi (misal setelah 1 minggu), sehingga server KSM tetap bersih tanpa membebani memori bot.

---

## 5. Daftar Tugas Implementasi (Task List)

**INGRESS & GATEWAY**
- [ ] Setup endpoint GitHub Webhooks dengan FastAPI.
- [ ] Implementasi *Pydantic Schema* untuk parsing payload GitHub dan *Jinja Templating* untuk notifikasi Discord.
- [ ] Implementasi sistem *Auto-Deploy* (menjalankan sintaks shell seperti `docker compose up` berdasarkan payload).
- [ ] Implementasi HMAC Webhook Signature, Deduplication, & Guardrails.

**AGENT & INFERENCE**
- [ ] Buat *Context & Date Resolver* (Pydantic).
- [ ] Rombak *in-memory history* menjadi modul Database dengan sistem *Rolling Summaries* (merangkum percakapan usang agar hemat token).
- [ ] Validasi *context length* maksimal 8,192 token sebelum request dikirim ke llama-server.
- [ ] Pembuatan knowledge base *Datasheet Perangkat IoT* dan *Modul Ajar* (chunking PDF dokumen AIoT ke dalam `pgvector`).
- [ ] *(Low Priority)* Implementasi **Streaming Responses** (`stream=True`). **Catatan:** Berisiko tinggi memicu *Rate Limit* Discord, sehingga bukan prioritas utama saat ini.
- [ ] Implementasi **Semantic Tool Routing (Tool Retrieval / RAG Router)**. Mencegah penuhnya *context window* dengan cara memfilter dan hanya memasukkan skema/deskripsi *tools* MCP yang relevan (menggunakan *vector search*) ke dalam *system prompt*.
- [ ] Tambahkan **Robust Error Handling (Exponential Backoff)** menggunakan library `tenacity` saat berkomunikasi dengan LLM atau MCP.

**TOOL EXECUTOR & DB (CORE)**
- [ ] Integrasi Pydantic untuk validasi skema input/output *tool*.
- [ ] Tambah *Audit Logging* (catat *user ID* dan *tool* yang dipakai).
- [ ] Setup koneksi PostgreSQL *async* & buat tabel utama (`mcp_tools`, `knowledge_base`, `thread_conversations`, `webhook_mappings`, `audit_logs`, `member_points`, `lab_inventory`).
- [ ] Implementasi **Parallel Tool Execution** menggunakan `asyncio.gather` agar eksekusi *multiple-tools* berjalan serentak.
- [ ] Pembuatan dasbor/sistem **Observability & Token Metrics** untuk mencatat statistik penggunaan token LLM dan frekuensi pemakaian tool per *member*.

**DISCORD COGS & USER FEATURES**
- [ ] Pembuatan Cog *Community*: Sistem Onboarding, Absensi `/hadir_vc`, dan *Gamification Leaderboard*.
- [ ] Pembuatan Cog *Utilities*: Polling dinamis, Manajemen *Discord Threads* (pembuatan & auto-archive), dan Notulensi Pintar.
- [ ] Pembuatan Cog *Scheduler*: Sinkronisasi kalender dan *blast* pengingat rapat (`discord.ext.tasks`).
- [ ] Pembuatan Cog *Lab Assistant*: *Tool* untuk query Inventaris Lab IoT dan monitoring status Sensor (*Snapshot* suhu/kelembaban).
- [ ] (Future) Pembuatan *tool* eksekusi fisik (contoh: MQTT *publish* ke relay ESP32) berserta *role permission checker*.

**WEB UI DASHBOARD (ADMIN PANEL)**
- [ ] Rancang dan bangun **Web Dashboard GUI** untuk memanajemen konfigurasi Nexo tanpa harus menyentuh kode.
- [ ] **Knowledge Base Manager**: Fitur UI untuk *upload*, hapus, dan kelola dokumen/materi yang akan masuk ke sistem RAG (Vektor DB).
- [ ] **MCP Server Manager**: Fitur antarmuka untuk menambahkan, mengedit, atau menghapus berbagai *endpoint URL* MCP Server IoT secara dinamis dan menyimpannya langsung ke database.
