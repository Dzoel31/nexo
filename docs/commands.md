# Command Nexo

Halaman ini berisi command yang dapat digunakan langsung di Discord. Untuk panduan singkat, mulai dari [Mulai menggunakan Nexo](getting-started.md).

Nexo menerima command dengan awalan `$` dan slash command dengan awalan `/`. Command tertentu hanya dapat digunakan oleh pengelola server.

## Command umum

| Command | Contoh | Kegunaan |
| --- | --- | --- |
| `$help`, `/help` | `$help` | Membuka panduan interaktif. |
| `$ping` | `$ping` | Memeriksa latensi bot ke Discord Gateway. |
| `$status` | `$status` | Memeriksa status layanan Nexo. |
| `$tools`, `/tools` | `$tools` | Menampilkan kemampuan tambahan yang sedang aktif. |
| `$sync` | `$sync` | Memperbarui daftar slash command; khusus owner. |
| `$clear [limit]` | `$clear 50` | Menghapus pesan jika pengguna memiliki izin Manage Messages. |
| `$reset`, `/reset` | `$reset` | Menghapus memory percakapan pengguna. |
| `$reset all` | `$reset all` | Menghapus memory global; memerlukan Manage Messages. |

`$help` memiliki beberapa halaman bantuan. Menu hanya dapat digunakan oleh pengguna yang membukanya.

## Percakapan dan statistik AI

Mention Nexo untuk percakapan natural. Untuk pertanyaan eksplisit, gunakan:

```text
/tanya pertanyaan: Bagaimana status project smart hydroponic?
```

Jika Nexo sedang menjawab pertanyaan lain, pertanyaanmu masuk antrean. `/tanya` memiliki jeda lima detik untuk setiap pengguna di server yang sama.

Gunakan command berikut untuk melihat konsumsi token:

```text
$tokenstats
/token-stats
$tokenleaderboard
/leaderboard-token
```

`tokenstats` menampilkan prompt token, completion token, total token, jumlah interaksi, dan rata-rata token per interaksi. Leaderboard menampilkan sepuluh pengguna teratas di server.

## Mengirim dan menjadwalkan pesan

`$say` mengirim pesan atas nama Nexo. Command ini memerlukan izin `Manage Messages` atau salah satu role pengelola yang dikonfigurasi, seperti `Leader`, `Co-Leader`, `Staff-Core`, atau `Admin`.

Format umumnya adalah:

```text
$say to <channel> [opsi] <isi pesan>
```

`to` bersifat opsional, tetapi menuliskannya membuat command lebih mudah dibaca. Channel tujuan dapat ditulis dalam tiga bentuk:

- mention channel, misalnya `#pengumuman`;
- ID channel, misalnya `1520017240097951774`;
- nama channel, misalnya `pengumuman`.

Contoh pengiriman langsung:

```text
$say to #pengumuman Rapat dimulai pukul 19.00 WIB.
$say 1520017240097951774 Rapat dimulai pukul 19.00 WIB.
$say to pengumuman Jangan lupa mengisi presensi.
```

### Mengirim pesan embed

Ya, Nexo bisa mengirim pesan embed, termasuk embed yang dijadwalkan. Tambahkan opsi `--embed` pada isi command. Judul embed dapat ditentukan dengan `--title`:

```text
$say to #pengumuman --embed --title "Pengingat rapat" Jangan lupa hadir pukul 19.00 WIB.
```

Nexo mengirim isi setelah opsi sebagai `description` embed. Jika `--title` tidak digunakan, embed tetap dibuat tanpa judul khusus. Contoh tanpa judul:

```text
$say to #pengumuman --embed Pengumuman ini dikirim dalam format embed.
```

Format embed hanya mengubah tampilan pesan; mention di dalam isi tetap diproses oleh Nexo. Gunakan format Discord seperti `@role`, `@nama`, atau mention channel sesuai kebutuhan.

### Menjadwalkan pesan

Pesan dapat dijadwalkan dengan waktu absolut menggunakan `--time` atau waktu relatif menggunakan `--in`. Untuk saat ini, `--in` menerima angka yang diikuti satu huruf satuan berikut:

| Satuan | Arti | Contoh |
| --- | --- | --- |
| `m` | menit | `--in 30m` |
| `h` | jam | `--in 2h` |
| `d` | hari | `--in 1d` |

Penulisannya harus menggunakan singkatan `m`, `h`, atau `d`. Bentuk kata lengkap seperti `30min`, `2hour`, atau `1day` belum didukung. Satuan detik juga belum tersedia, sehingga `--in 30s` tidak akan dikenali sebagai jadwal. Huruf besar dan kecil diterima, jadi `2H` juga dapat digunakan.

```text
$say to #pengumuman --time "2026-11-01 19:00" Rapat evaluasi.
$say to #pengumuman --in 30m Pengingat: kumpul di ruang meeting.
$say to #pengumuman --in 2h --embed --title "Pengingat" Agenda dimulai dua jam lagi.
$say to #pengumuman --in 1d Pengingat: agenda berlangsung besok.
$say to #pengumuman --time "2026-11-01 19:00" --embed --title "Rapat evaluasi" Jangan lupa hadir.
```

Nilai `--in` dihitung mulai dari waktu saat command diproses. `--in 30m` berarti sekitar 30 menit dari sekarang, sedangkan `--in 2h` berarti sekitar dua jam dari sekarang. Format waktu absolut menggunakan `YYYY-MM-DD HH:MM` dan dipahami sebagai WIB. Nexo mengubahnya ke UTC sebelum menyimpannya sehingga pengiriman tetap konsisten dengan timezone server.

Setelah command diterima, Nexo:

1. memeriksa channel tujuan dan memastikan waktu berada di masa depan;
2. menyimpan isi pesan, format biasa atau embed, judul, channel, pembuat, dan waktu ke database;
3. mengembalikan UUID jadwal dan timestamp Discord;
4. memeriksa jadwal yang sudah jatuh tempo setiap 20 detik;
5. mengirim pesan ke channel tujuan dan menandai jadwal sebagai `sent`.

Karena pemeriksaan berjalan setiap 20 detik, pesan dapat terkirim dalam rentang hingga sekitar 20 detik setelah waktu yang ditentukan. Jika channel tidak ditemukan atau pengiriman gagal, jadwal ditandai `failed`.

Gunakan command berikut untuk mengelola jadwal:

```text
$say list
$say cancel 550e8400-e29b-41d4-a716-446655440000
```

`$say list` menampilkan jadwal yang masih menunggu, termasuk ID, channel, waktu, format, dan cuplikan pesan. Untuk membatalkan jadwal, gunakan UUID yang diberikan saat pembuatan atau ditampilkan oleh `$say list`. Jadwal yang sudah berstatus `sent` atau `failed` tidak dapat dibatalkan.

## Voice channel

Untuk melihat anggota yang sedang berada di voice channel:

```text
$voice
$voice Lab IoT
/voice channel_name: Lab IoT
```

Tanpa nama, Nexo memakai channel tempat command dijalankan atau channel voice yang sedang digunakan pengguna.

## Radar kompetisi

Radar kompetisi tersedia sebagai slash command:

```text
/lomba add nama:"Gemastik XIX 2026" deadline:"2026-10-15 23:59" kategori:AI
/lomba list
/lomba list kategori:IoT
/lomba detail id:12
/lomba delete id:12
```

Deadline ditulis dalam format `YYYY-MM-DD` atau `YYYY-MM-DD HH:MM` dan diproses sebagai WIB. Reminder otomatis berjalan setiap 30 menit. Penambahan dan penghapusan kompetisi memerlukan izin pengelola.
