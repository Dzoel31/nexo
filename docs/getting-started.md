# Mulai menggunakan Nexo

Nexo digunakan langsung dari server Discord. Pastikan kamu berada di server yang sudah memasang Nexo, lalu buka channel tempat bot dapat membaca dan mengirim pesan.

## Tiga langkah pertama

1. Ketik `$help` atau gunakan `/help`.
2. Pilih kategori bantuan yang ingin dilihat.
3. Jalankan command yang sesuai, atau mention Nexo dan jelaskan kebutuhanmu.

Contoh percakapan:

```text
Nexo, siapa saja yang sedang ada di voice channel Lab IoT?
```

Nexo akan mencoba memahami permintaan tersebut dan memilih bantuan yang sesuai. Untuk membuat agenda, sertakan tanggal, jam, topik, dan lokasi agar Nexo tidak perlu menebak.

## Command yang sering dipakai

| Kebutuhan | Gunakan | Contoh |
| --- | --- | --- |
| Membuka bantuan | `$help` atau `/help` | `$help` |
| Bertanya kepada Nexo | `/tanya` atau mention | `/tanya pertanyaan: Apa kabar project hidroponik?` |
| Memeriksa bot | `$ping` | `$ping` |
| Melihat tools yang aktif | `$tools` atau `/tools` | `$tools` |
| Melihat anggota voice channel | `$voice` atau `/voice` | `$voice Lab IoT` |
| Menghapus ingatan percakapan | `$reset` atau `/reset` | `$reset` |

## Membuat pengumuman

Pengelola server dapat mengirim pesan melalui Nexo:

```text
$say to #pengumuman Rapat dimulai pukul 19.00 WIB.
```

Pesan juga dapat dibuat dalam bentuk embed:

```text
$say to #pengumuman --embed --title "Pengingat rapat" Jangan lupa hadir.
```

Untuk mengirimnya nanti, tambahkan `--in`:

```text
$say to #pengumuman --in 30m Pengingat: kumpul di ruang meeting.
```

Detail format waktu, embed, daftar jadwal, dan pembatalan tersedia di halaman [Command](commands.md).

## Membuat event

Kamu dapat meminta Nexo membuat event menggunakan bahasa natural:

```text
Nexo, buat rapat evaluasi besok jam 8 malam di Voice Channel Lab IoT.
```

Jika informasi penting belum disebutkan, Nexo akan meminta detail yang kurang. Berikan tanggal, jam, topik, dan lokasi pada balasan berikutnya.

## Jika command tidak berhasil

Periksa hal berikut:

- gunakan `$help` untuk memastikan nama command benar;
- pastikan Nexo memiliki izin membaca dan mengirim pesan di channel tersebut;
- pastikan kamu memiliki izin pengelola untuk command seperti `$say`, `$clear`, dan pengelolaan lomba;
- gunakan format waktu yang dicontohkan;
- jika Nexo sedang memproses pertanyaan lain, tunggu sampai antrean selesai.

Jika masalah tetap terjadi, kirimkan command yang digunakan dan pesan error kepada pengelola server.
