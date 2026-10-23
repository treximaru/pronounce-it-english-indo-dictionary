# SPEK PROTOTYPE — Kamus Pronunciation Hybrid v1
**Keputusan terkunci: 23 Oktober 2026**
Pemilik: Abdulaziz — Arsitektur audio: **HYBRID (kamus offline + TTS bawaan HP dulu, cloud menyusul)**

---

## 1. Arsitektur Final Prototype

```
┌─ APK (Flutter) ─────────────────────────────────────────┐
│  Database SQLite di dalam HP (offline 100%)            │
│  isinya: kata, IPA UK, syllable+stress, POS,            │
│          definisi EN, contoh kalimat, gloss ID (jika ada)│
│                                                         │
│  Audio: Android TextToSpeech bawaan HP                  │
│         Locale: en-GB (UK = default utama)              │
│         Kecepatan: Normal (1.0x) & Lambat (0.6x)        │
│         Target: kata DAN kalimat contoh                 │
│                                                         │
│  (Nanti, v2) Cloud TTS UK via backend cache —           │
│  disiapkan slot-nya dari sekarang, belum diaktifkan     │
└─────────────────────────────────────────────────────────┘
Tidak ada: server, login, API key, biaya, Google Translate endpoint tidak resmi.
```

## 2. Ruang Lingkup Prototype (yang dibangun pertama)
- **1.000 kata** terumum (inti daftar frekuensi — kata yang paling sering dipakai siswa)
- Layar: Beranda (cari) → Hasil → Detail Kata → Favorit
- Detail kata persis format konsep: IPA UK, syllable, stress, cara baca sederhana, definisi EN, contoh kalimat, gloss ID bila ada
- Tombol audio di: kata (normal), kata (lambat), kalimat (normal), kalimat (lambat)
- Deteksi otomatis: jika HP belum punya suara en-GB, aplikasi menampilkan panduan 1x download suara UK di Pengaturan Android (langkah bergambar, bahasa Indonesia)
- Favorit & riwayat pencarian tersimpan lokal

## 3. Yang TIDAK masuk prototype
- Cloud TTS (v2), quiz (v2/v3), Word of the Day (v2), audio rekaman manusia Wiktionary (v2 — slot disiapkan)
- Aksen US (pengaturan disiapkan, default mati; UK dulu sesuai keputusan)

## 4. Pipeline Data
1. Ambil dump English Wiktionary dari Kaikki.org (JSON per kata: definisi, IPA, contoh, terjemahan ID, link audio)
2. Gabung Open English WordNet (definisi bersih + sinonim)
3. Syllable + stress dari CMUdict + pemecah suku kata berbasis aturan untuk IPA UK
4. Saring 1.000 kata teratas (ranking frekuensi ECDICT/BNC) → SQLite + FTS5
5. Uji acak 50 kata manual oleh pemilik (guru) sebelum APK dibagikan ke siswa

## 5. Cek Lingkungan Build (dilakukan 23 Okt 2026, jujur apa adanya)
- VM ini: **Flutter & Android SDK BELUM terpasang**, Java 17 ada (Temurin di ~/workspace/tools/android), disk kosong 86 GB, RAM 7,7 GB (ketat tapi cukup untuk build release 1 aplikasi)
- Rencana: install Flutter SDK + Android SDK **di bawah ~/workspace/tools/** (bukan system) supaya **tidak hilang saat VM replace** — pola yang sama seperti Go & toolchain APK sebelumnya yang terbukti awet
- Estimasi unduhan toolchain: ±3–4 GB, sekali saja

## 6. Urutan Kerja Berikutnya
1. ✅ Konsep & arsitektur terkunci (hybrid)
2. ⏭️ Install toolchain Flutter/Android di workspace
3. ⏭️ Bangun pipeline data → SQLite 1.000 kata, verifikasi sampel datanya ditampilkan ke pemilik
4. ⏭️ Bangun APK prototype → pemilik tes di HP sendiri (Redmi Note 11): kualitas TTS UK bawaan HP-nya = penentu lanjut/tidak
5. ⏭️ Revisi dari tes pemilik → naik ke 100.000+ kata (v2 sekalian cloud)

## 7. Kriteria Prototype Dinyatakan Berhasil
- Cari kata < 1 detik, offline (mode pesawat menyala)
- Klik kata → bunyi UK keluar; klik kalimat → terbaca natural; mode lambat bekerja
- IPA + syllable + stress tampil benar pada 50 kata uji
