# Aturan Pengembangan KSM AIoT Bot

Kumpulan aturan ini akan otomatis dimuat oleh AI (Nexo / sistem) setiap kali bekerja di *workspace* ini. Harap patuhi standar berikut:

## 1. Manajemen Paket (Package Management)
- **WAJIB** menggunakan `uv` untuk manajemen modul Python.
- Dilarang keras menggunakan `pip install` langsung. Gunakan `uv add <package>` untuk menginstal dependensi baru agar terpusat dan sangat cepat.
- Dilarang keras mengubah versi Python tanpa persetujuan eksplisit dari *owner*.

## 2. Struktur Proyek & Penamaan File (Cogs)
- Proyek ini memisahkan fitur menggunakan fitur ekstensi dari `discord.py` yaitu **Cogs**.
- Semua *Cog* diletakkan di dalam folder `cogs/`.
- Penamaan file Cog harus spesifik dengan fungsinya, hindari penamaan generik (seperti `discord_tools.py` atau `utils.py`). 
  - ✅ Benar: `server_events.py` (untuk event Discord), `user_data.py` (untuk mengambil data profil), `mcp_router.py`.
  - ❌ Salah: `bot_commands.py`, `tools.py`.

## 3. Tool LLM & Pydantic
- Setiap fitur lokal (Discord) yang ingin dieksekusi oleh LLM **WAJIB** didefinisikan skemanya menggunakan **Pydantic**.
- Model Pydantic wajib memiliki deskripsi (`Field(description="...")`) yang jelas agar LLM memahami format apa yang harus dikeluarkan.
- Kode eksekutor *tool* (`handler`) dipisahkan ke dalam *methods* pada *class* Cog terkait.
- Context Window untuk LLM saat ini adalah 8,192 tokens.
- Model yang digunakan adalah Gemma 4 E2B GGUF Q4_K_M. Jumlah parameter 2.3B effective (5.1B dengan embeddings)

## 4. Tone of Voice
- Ketika menulis pesan statis atau memperbarui *system prompt*, selalu pertahankan gaya bahasa Indonesia yang **santai, kasual, namun tetap profesional**. Gunakan emoji secara natural.
- Hindari bahasa baku bergaya robot.

## 5. Kepatuhan Discord API & Asynchronous
- Pastikan implementasi kode selalu patuh terhadap aturan resmi Discord (Developer ToS) dan batasan *rate limit*.
- **Rate Limit Headers:** Discord mengembalikan header seperti `X-RateLimit-Remaining` dan `X-RateLimit-Reset`. Pustaka `discord.py` sudah menangani ini secara otomatis (*under the hood*), jadi jangan membuat sistem *rate-limit* manual untuk fungsi standar.
- **Pencegahan Spam:** Walaupun `discord.py` mencegah kita terkena *banned* dengan melakukan *auto-sleep* saat terkena 429 (Too Many Requests), **AI dilarang keras** membuat kode yang melakukan *looping* pemanggilan API Discord (seperti mengirim ribuan DM atau mengedit pesan ratusan kali dalam sedetik) tanpa menyisipkan `asyncio.sleep()`.
- Biasakan merujuk pada dokumentasi resmi `discord.py` untuk menghindari penggunaan API yang usang (*deprecated*).
- Sangat berhati-hati dalam membedakan proses eksekusi **async** (non-blocking) dan **sync** (blocking). Dilarang keras menaruh operasi *sync* yang memakan waktu lama di dalam *event loop* `discord.py` karena dapat membuat bot *freeze* atau *timeout*!

## 6. Linting & Formatting (Wajib)
- **AI (Nexo) WAJIB** menjalankan proses *linting* dan *formatting* menggunakan `ruff` (`uv run ruff check --fix .` dan `uv run ruff format .`) setiap kali selesai menulis atau mengubah kode Python jika dibutuhkan (perubahan besar).
- AI tidak boleh berhenti memperbaiki kode sebelum memastikan kode tersebut lolos uji *linter* (status *checked* atau *passed*), dan harus secara proaktif menangani error yang muncul akibat perubahannya.
