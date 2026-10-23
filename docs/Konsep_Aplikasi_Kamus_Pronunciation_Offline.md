# KONSEP APLIKASI
## Kamus Bahasa Inggris English–English + Pronunciation
### Full Offline — Fokus Membantu Siswa Membaca & Mengucapkan Kata

**Pemilik Project:** Abdulaziz (Muhammad Abdul Aziz, S.Pd) — Guru Bahasa Inggris, SMK Panca Bhakti Banjarnegara
**Tanggal konsep:** 23 Oktober 2026
**Status:** Konsep awal v1.0 — untuk didiskusikan sebelum pembuatan prototype

---

## 1. Ide Inti (Satu Kalimat)

Aplikasi kamus di HP Android yang **tanpa internet sama sekali** bisa dipakai siswa untuk mencari kata bahasa Inggris, melihat cara bacanya secara tertulis (IPA + pecahan suku kata / syllable + tekanan kata), membaca arti English–English yang sederhana, melihat contoh kalimat, dan **sekali klik langsung mendengar pengucapannya** — kata per kata maupun satu kalimat penuh secara natural.

> Prinsip utama: **Klik kata = bunyi keluar.** Tidak ribet, tidak perlu internet, tidak perlu login.

---

## 2. Masalah yang Diselesaikan

1. Siswa tahu arti kata (dari Google Translate) tapi **tidak bisa mengucapkannya**.
2. Kamus online & Google Translate butuh internet — tidak selalu tersedia di kelas / di rumah.
3. Kamus kertas ada IPA-nya, tapi siswa **tidak paham cara membaca IPA** dan tidak ada bunyinya.
4. Siswa malu bertanya / malu latihan mengucapkan di depan orang.

Aplikasi ini menjadi "guru pronunciation pribadi" di saku siswa.

---

## 3. Target Pengguna

- **Utama:** Siswa SMP / SMK (konteks awal: siswa SMK Panca Bhakti Banjarnegara & English Club)
- **Pendukung:** Guru bahasa Inggris untuk demonstrasi di kelas (bisa ditampilkan via proyektor / speaker)

---

## 4. Fitur Utama

### 4.1 Pencarian Kata (Search)
- Ketik kata → muncul saran otomatis (autocomplete) walau offline
- Toleran salah ketik ringan (misal "educasion" → disarankan "education")
- Riwayat pencarian & kata favorit (bookmark)

### 4.2 Halaman Kata — Ini Jantung Aplikasinya
Setiap kata ditampilkan seperti contoh ini:

---
**education**  `noun`  [ ▶ DENGAR ]

- **Pronunciation (UK):** /ˌedʒuˈkeɪʃn/  [ ▶ ]
- **Pronunciation (US):** /ˌedʒəˈkeɪʃn/  [ ▶ ]
- **Pecahan suku kata (syllable):** **ed · u · ca · tion** (4 suku kata)
- **Tekanan kata (stress):** di suku kata ke-3 → ed-u-**CA**-tion
- **Cara baca sederhana (untuk siswa Indonesia):** "ej-u-**KEY**-syən" — panduan perkiraan, IPA tetap yang utama
- **Arti (English–English, bahasa sederhana):**
  > the process of teaching and learning, usually at school or university
- **Contoh kalimat:**
  > "Education is important for everyone." [ ▶ Dengar kalimat — mode normal ]
  > [ ▶ Dengar kalimat — mode lambat / slow ]
- **Bentuk kata terkait:** educate (verb), educational (adjective), educator (noun)

---

### 4.3 Audio — Fitur yang Paling Diinginkan Pemilik Project
- **Klik ikon speaker pada kata** → audio pengucapan kata langsung diputar
- **Klik ikon speaker pada kalimat** → kalimat dibacakan **utuh & natural** (bukan kata-per-kata terputus)
- Pilihan kecepatan: **Normal** dan **Lambat (Slow)** — mode lambat khusus untuk latihan
- Pilihan aksen: **British (UK)** dan **American (US)** — bisa dipilih di pengaturan, dan bisa dibandingkan di halaman kata
- Semua audio bekerja **100% offline**

### 4.4 Fitur Pendukung (Tahap Berikutnya)
- **Word of the Day** — 1 kata baru setiap hari di halaman depan
- **Daftar Oxford 3000 / 5000** — daftar kata terpenting, bisa dipelajari per tema / per abjad
- **Latihan (Quiz) Pronunciation mini:** dengarkan audio → tebak kata / pilih ejaan yang benar
- **Favorit & Daftar Belajar Saya** — siswa menyimpan kata sulitnya sendiri

---

## 5. Hal Teknis Terpenting: Dari Mana Isi Kamusnya?

Ini yang harus jujur sejak awal:

### 5.1 Soal Nama & Isi "Oxford"
Isi kamus Oxford yang asli (definisinya kata-per-kata) adalah **karya berhak cipta Oxford University Press**. Kita **tidak boleh menyalin & membungkus ulang seluruh isi Oxford** ke dalam APK lalu menyebarkannya — itu pelanggaran hak cipta, dan APK-nya bisa ditolak Play Store / ditakedown.

**Solusinya ada 3 jalan, konsep ini memakai jalan B + C:**

- **A. Lisensi resmi Oxford** — legal penuh, tapi berbayar & prosesnya untuk penerbit. Tidak realistis untuk tahap awal.
- **B. Gaya & daftar kata Oxford, isi dari sumber terbuka (REKOMENDASI)** — Memakai daftar **Oxford 3000™ / Oxford 5000™** sebagai *daftar kata prioritasnya* (kata apa saja yang harus ada duluan), tapi definisi, IPA, syllable, dan contoh kalimat diambil dari sumber **open-license** di bawah. Tampilan & rasa pemakaiannya seperti kamus Oxford, isinya legal untuk disebar.
- **C. Untuk pemakaian internal sekolah saja** — prototype awal boleh dipakai terbatas untuk uji coba di kelas sendiri sambil jalurnya diluruskan ke B.

### 5.2 Sumber Data Terbuka yang Akan Dipakai (semua bisa offline)
| Kebutuhan | Sumber | Keterangan |
|---|---|---|
| Definisi English–English | Wiktionary (via Kaikki.org) + Princeton WordNet | Lengkap, gratis, lisensi terbuka (CC BY-SA / WordNet License) |
| IPA / cara baca tertulis | Wiktionary + CMU Pronouncing Dictionary | CMUdict: ±134.000 kata dengan penanda syllable & stress |
| Pecahan syllable | CMUdict + aturan hyphenation | ed·u·ca·tion, lengkap dengan stress |
| Contoh kalimat | Wiktionary examples + Tatoeba | Kalimat contoh nyata, lisensi terbuka |
| Daftar kata prioritas | Oxford 3000 / 5000 word list | Urutan belajar: kata paling sering dipakai didahulukan |

> Dengan kombinasi ini cakupannya bisa **100.000+ kata** — untuk kebutuhan siswa SMP/SMK, ini praktis terasa "selengkap-lengkapnya".

### 5.3 Soal Audio Offline — Keputusan Desain Paling Penting
Menyimpan file audio manusia asli untuk 100.000+ kata itu **tidak masuk akal ukurannya**: 1 kata ≈ 15 KB → 100.000 kata ≈ 1,5 GB, itu baru kata, belum kalimat (kalimat tidak mungkin direkam semuanya).

**Solusi yang dipakai: Mesin suara offline di dalam aplikasi (Offline TTS Neural)**
- Memakai model suara kecil modern (kelas **Piper TTS / Kokoro** — open source) yang ditanam di APK
- Bisa membacakan **kata apa pun & kalimat apa pun** — termasuk kalimat contoh yang baru — secara natural, tanpa file audio per kata
- Ukuran model suara: ± 40–80 MB per aksen (UK + US)
- Kecepatan bisa diatur (normal / lambat) tanpa mengubah file
- **Kelebihan:** cakupan 100% — tidak ada kata yang "tidak ada audionya"
- **Kekurangan jujur:** suara hasil mesin, bukan rekaman manusia asli Oxford. Untuk kata tunggal kualitasnya sangat baik & jelas; untuk pengajaran pronunciation tingkat lanjut, guru tetap jadi rujukan akhir.

*Opsi hybrid tahap lanjut:* untuk 3.000 kata teratas (Oxford 3000), bisa ditambahkan rekaman suara manusia asli dari sumber terbuka (Lingua Libre / Wiktionary audio) sebagai audio utama, TTS jadi cadangan. Ukuran tambahan ± 50 MB.

---

## 6. Perkiraan Ukuran & Bentuk APK

| Komponen | Perkiraan ukuran |
|---|---|
| Aplikasi (Flutter) + database kamus terkompresi (100rb+ kata, definisi + IPA + contoh) | 120 – 180 MB |
| Model suara offline UK | 40 – 60 MB |
| Model suara offline US | 40 – 60 MB |
| **Total APK full offline** | **± 200 – 300 MB** |

- Format distribusi awal: **file APK langsung (sideload)** — dibagikan ke siswa via WhatsApp / flashdisk / ShareIt, sesuai keinginan "full APK offline". Ukuran ini wajar untuk APK full-offline.
- Jika nanti naik Play Store: pakai format AAB + Play Asset Delivery agar tidak kena batas ukuran APK.
- HP target: Android 8 ke atas, RAM 3 GB — mayoritas HP siswa sudah memenuhi.

---

## 7. Teknologi yang Diusulkan

- **Framework:** Flutter (1 kode, tampilan konsisten, performa pencarian cepat)
- **Database offline:** SQLite + FTS5 (pencarian full-text super cepat, tetap di dalam HP)
- **Audio:** Piper / Kokoro TTS offline (plugin Flutter), mode normal & slow
- **Tanpa:** server, login, internet, iklan — aplikasi bersih untuk sekolah

---

## 8. Tahapan Pembuatan (Roadmap)

### Tahap 1 — Prototype (Pembuktian Konsep)
- 1.000 kata paling umum dulu (inti Oxford 3000)
- Fitur: cari kata → IPA + syllable + arti + contoh kalimat → klik = audio kata & kalimat (UK & US, normal & slow)
- Tujuan: pemilik project bisa mencoba langsung di HP & menilai kualitas suaranya dulu

### Tahap 2 — Kamus Lengkap
- Naik ke 100.000+ kata dari data terbuka
- Favorit, riwayat, Word of the Day, daftar Oxford 3000/5000 per tema

### Tahap 3 — Penyempurnaan
- Quiz pronunciation, daftar belajar, (opsional) audio manusia untuk 3.000 kata teratas
- Uji ke siswa (English Club sebagai kelompok uji pertama sangat cocok)

---

## 9. Keputusan yang Perlu Dipilih Pemilik Project

1. **Nama aplikasi:** usulan — *SpeakDict*, *PronounceDict*, atau *Kamus Pintar: English Pronunciation*. Nama "Oxford" tidak dipakai sebagai nama resmi (alasan hak cipta di 5.1), tapi di deskripsi bisa ditulis "berbasis daftar kata Oxford 3000".
2. **Mulai dari mana:** Prototype 1.000 kata dulu **(sangat disarankan)** vs langsung lengkap — langsung lengkap risikonya: lama, dan kalau kualitas suara ternyata tidak cocok, bongkar besar.
3. **Aksen utama default:** UK (British, standar buku pelajaran Indonesia) atau US?

---

## 10. Ringkasan Janji Konsep Ini

✅ English–English, fokus pronunciation: IPA + syllable + stress + cara baca sederhana
✅ Klik kata → bunyi; klik kalimat → dibacakan natural; ada mode lambat
✅ 100% offline dalam satu APK (± 200–300 MB)
✅ Isi legal dari sumber terbuka, cakupan 100.000+ kata, prioritas Oxford 3000/5000
⚠️ Bukan salinan isi Oxford asli (hak cipta) — gaya & daftar prioritasnya Oxford, isinya open-license
⚠️ Audio = suara mesin neural offline berkualitas tinggi, bukan rekaman manusia Oxford — supaya semua kata & semua kalimat bisa bersuara tanpa APK jadi bergiga-giga

