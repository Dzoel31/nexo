# Cara kerja chatbot LLM

Percakapan dapat dimulai dengan mention atau `/tanya`. Nexo memeriksa kesehatan provider LLM, menaruh pertanyaan ke `message_queue`, lalu memberi tahu posisi antrean jika ada permintaan lain. Satu worker mengambil item antrean dan memakai lock bot agar pemrosesan berjalan teratur.

Sebelum worker dipakai, Nexo memuat system prompt dari `prompts/system_prompt.md`, mengambil daftar tools MCP melalui SSE, menggabungkannya dengan local Discord tools, lalu membersihkan schema JSON agar ukuran konteks lebih kecil. Riwayat percakapan pengguna dibaca dari database dan dipakai sebagai konteks.

```mermaid
sequenceDiagram
    actor User as Pengguna
    participant Discord
    participant Queue as Message queue
    participant Agent as Agent worker
    participant LLM as LLM API
    participant Tool as Local/MCP tool
    participant DB as Conversation DB

    User->>Discord: Mention atau /tanya
    Discord->>Queue: Simpan pertanyaan
    Agent->>DB: Ambil riwayat dan simpan pesan user
    Agent->>LLM: Kirim prompt, konteks, dan function tools
    alt Model meminta tool
        LLM-->>Agent: Tool call + argumen
        Agent->>Tool: Jalankan handler
        Tool-->>Agent: Hasil tool
        Agent->>LLM: Kirim hasil tool
    end
    LLM-->>Agent: Jawaban akhir
    Agent->>DB: Simpan jawaban dan token usage
    Agent-->>Discord: Embed respons Nexo
```

Model memilih tool berdasarkan intent. Misalnya, pertanyaan tentang anggota voice channel dapat memanggil `check_voice_channel`, sedangkan permintaan membuat event dapat memanggil `create_discord_event`. Untuk beberapa kebutuhan dalam satu pesan, system prompt meminta model memanggil tool yang relevan secara paralel.

Jawaban ditampilkan sebagai embed Discord dengan durasi proses dan informasi token jika provider mengembalikannya. Jika LLM atau tool gagal, pengguna menerima pesan error dan kegagalan dicatat melalui logger.
