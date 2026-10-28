# Nexo KSM AIoT

Nexo adalah bot Discord yang membantu kegiatan KSM AIoT. Kamu bisa bertanya tentang project, mengirim pengumuman, membuat pengingat, melihat anggota voice channel, mencatat lomba, dan menerima kabar terbaru dari GitHub.

Kamu tidak perlu mengetahui cara kerja di baliknya untuk menggunakan Nexo. Cukup gunakan command yang tersedia atau mention Nexo lalu tulis permintaanmu dengan bahasa sehari-hari.

## Mulai dari sini

Buka [Mulai menggunakan Nexo](getting-started.md) untuk melihat contoh penggunaan paling umum. Jika ingin melihat semua command, buka halaman [Command](commands.md).

Gunakan `$help` atau `/help` di Discord untuk membuka bantuan langsung dari Nexo. Bantuan tersebut menampilkan command yang tersedia di server dan fitur yang sedang aktif.
Untuk bantuan terperinci, gunakan `$help say to` atau berikan nama command
lainnya. Panduan deployment dan environment tersedia di
[Konfigurasi dan deployment](configuration.md).

## Contoh permintaan

```text
Nexo, bantu jelaskan status project smart hydroponic.
```

```text
Nexo, buat pengingat rapat besok jam 7 malam di channel pengumuman.
```

```text
$say to #pengumuman --in 30m Jangan lupa mengikuti briefing.
```

## Yang bisa dilakukan Nexo

- menjawab pertanyaan tentang project KSM AIoT;
- mengirim pesan biasa atau embed ke channel tertentu;
- menjadwalkan pengumuman untuk menit, jam, hari, atau waktu tertentu;
- membuat event, polling, dan thread;
- membuat voice channel sementara saat pengguna masuk ke channel generator;
- melihat anggota yang sedang berada di voice channel;
- menyimpan dan mengingatkan deadline lomba;
- menampilkan statistik penggunaan AI;
- mengirim notifikasi ketika ada perubahan pada project GitHub.

Penjelasan tentang cara kerja internal Nexo tersedia di bagian [Developer](architecture.md).

## Menjalankan dokumentasi

Pengelola project dapat menjalankan dokumentasi secara lokal dengan:

```powershell
uv run zensical serve
```

Untuk menghasilkan situs statis:

```powershell
uv run zensical build
```
