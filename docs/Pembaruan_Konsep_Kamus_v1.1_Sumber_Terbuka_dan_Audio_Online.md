# PEMBARUAN KONSEP v1.1 — 23 Oktober 2026
## Keputusan baru pemilik project
1. **Skip Oxford** — tidak wajib Oxford, pakai sumber terbuka, yang penting selengkap mungkin.
2. Kamus utama **English–English**. Bahasa Indonesia **boleh sebagai tambahan** (gloss kecil), bukan isi utama.
3. Aksen audio **utama UK (British)**.
4. Pertanyaan yang dijawab di dokumen ini: kalau audio pakai penyedia online seperti Google Translate sebagai backend — **bisa atau tidak, bagaimana caranya, legal atau tidak, ribet atau tidak?**

---

## A. Sumber Terbuka Pengganti Oxford (hasil cek)

| Sumber | Isi | Lisensi | Peran |
|---|---|---|---|
| **Kaikki.org / English Wiktionary** | Sumber terbesar: definisi EN, IPA (sering dibedakan UK/US), contoh kalimat, bentuk kata, terjemahan (termasuk ke Bahasa Indonesia untuk sebagian kata), link file audio rekaman manusia | CC BY-SA 4.0 + GFDL — wajib atribusi + share-alike | **Tulang punggung kamus** |
| **Open English WordNet (Princeton)** | 155.000–161.000 kata, definisi pendek yang rapi + contoh pemakaian, sinonim | BSD-like — sangat bebas | Pembersih/pelengkap definisi |
| **CMU Pronouncing Dictionary** | ±134.000 kata, fonem + jumlah syllable + stress | Bebas (public/BSD-style) | Data syllable & stress (aksen US, untuk pembanding) |
| **ECDICT** | 770rb+ (versi extended 2jt+) entri: fonetik, definisi EN, frekuensi BNC, penanda Oxford 3000, bentuk kata | MIT | Ranking frekuensi: kata terpenting tampil duluan. Terjemahannya Mandarin — diabaikan, field lain yang dipakai |
| **Free Dictionary API (dictionaryapi.dev)** | API online gratis berbasis Wiktionary, ada field phonetic + audio (contoh: hello → audio UK dari server Google dictionary) | Gratis, tanpa key | Untuk prototype online cepat / cek silang, bukan untuk dibundel massal |

**Kesimpulan data:** gabungan Kaikki + WordNet realistis 100.000+ kata bersih untuk siswa, dengan IPA UK untuk mayoritas kata umum. Terjemahan Indonesia dari Wiktionary cakupannya parsial (kata-kata umum saja) — pas untuk posisi "tambahan", bukan janji lengkap.

---

## B. Audio Online — 3 Jalan yang Sering Tertukar

### Jalan 1 — "Nempel" Google Translate langsung (translate_tts / gTTS) ❌ untuk produk, ⚠️ untuk coba-coba pribadi
- **Bisa?** Bisa, sangat mudah. Endpoint tidak resmi `translate.google.com/translate_tts?q=<teks>&tl=en` mengembalikan MP3. Library gTTS memakai cara ini.
- **Cara:** APK/server tinggal panggil URL itu tiap klik. 1 baris kode.
- **Legal?** **Abu-abu cenderung melanggar.** Google Translate adalah produk untuk pengguna akhir, bukan API untuk ditanam di aplikasi. Jawaban resmi di forum Google: untuk menanam Translate di aplikasi harus pakai API berbayar; produk Translate tidak untuk dipakai begitu. Audio dari endpoint tidak resmi ini lisensinya tidak jelas untuk penggunaan di aplikasi.
- **Ribet/risiko teknis:** endpoint tidak terdokumentasi → bisa berubah/patah sewaktu-waktu tanpa pemberitahuan; ada rate-limit tidak resmi (±429 setelah puluhan ribu karakter/jam per IP) → kalau 1 server dipakai banyak siswa, IP server kena blokir; tidak ada jaminan UK (parameter aksen terbatas/trik domain).
- **Putusan:** jangan jadikan fondasi APK yang disebar. Boleh hanya untuk eksperimen internal.

### Jalan 2 — Google Cloud Text-to-Speech API (RESMI, beda produk dari Translate) ✅
- **Bisa?** Bisa penuh, memang dijual untuk ini. Suara UK lengkap: en-GB Standard, WaveNet, Neural2, Chirp 3 HD (pria/wanita).
- **Cara (arsitektur wajib):**
  ```
  APK siswa → backend kecil kita (VPS Oracle Free / batam) → Google Cloud TTS (voice en-GB-Neural2)
             ← MP3 ← backend cache MP3 di disk ←
  APK memutar MP3 + menyimpan cache lokal di HP (klik kedua = offline, gratis)
  ```
  API key **tidak boleh** ditanam di APK (pasti bocor). Backend ±100 baris, tugasnya cuma meneruskan + cache. Karena kata kamus itu-itu saja, cache membuat 80–90% klik tidak perlu bayar lagi.
- **Legal?** **100% legal & berlisensi** untuk dipakai di aplikasi, termasuk komersial (larangannya hanya: tidak boleh dipakai melatih TTS pesaing).
- **Ribet?** Sedang: daftar Google Cloud + kartu untuk billing, aktifkan API, buat service account, deploy backend kecil. Sekali setup, selesai.
- **Biaya (harga resmi Google Cloud, dicek 23 Okt 2026):**
  - Standard/WaveNet: **$4 / 1 juta karakter**, gratis 4 juta karakter/bulan
  - Neural2: **$16 / 1 juta karakter**, gratis 1 juta karakter/bulan
  - Chirp 3 HD: $30 / 1 juta karakter, gratis 1 juta/bulan
  - Hitungan kamus: pre-generate 10.000 kata + kalimat contohnya ≈ 500rb karakter → **masuk kuota gratis / < $8 sekali buat**. Pemakaian live per siswa pun murah karena 1 kata cuma ±7 karakter & ada cache 2 lapis.
- **Alternatif resmi setara:** Microsoft Azure Speech (en-GB Sonia/Ryan Neural, gratis 500rb karakter/bln), Amazon Polly (en-GB Amy/Brian/Arthur, $4–$16/1jt). Arsitekturnya sama persis.

### Jalan 3 — TTS Bawaan HP Android Sendiri (Google Speech Services di HP siswa) ✅✅ Paling tidak ribet
- **Bisa?** Bisa. Android punya API TextToSpeech resmi. APK tinggal perintah: bicara teks ini, Locale = UK.
- **Cara:** tidak ada backend, tidak ada API key, tidak ada biaya, tidak ada server. Di Flutter pakai plugin flutter_tts, beberapa baris.
- **Legal?** **100% legal** — memang API sistem yang disediakan untuk aplikasi.
- **Kekurangan jujur:** kualitas & persisnya suara tergantung HP masing-masing siswa; sebagian HP perlu download data suara en-GB sekali (online) baru setelah itu bisa offline. Suara tidak seragam antar-siswa.
- **Kelebihan besar:** setelah suara terdownload, ini **bekerja offline** — jadi problem "offline susah" sebenarnya terpecahkan untuk audio tanpa model besar di APK.

### Bonus Jalan 4 — Rekaman Manusia UK dari Wiktionary / Lingua Libre
Banyak kata umum sudah punya rekaman suara manusia UK asli (file .ogg/.mp3, lisensi CC). Kalau online / sudah terdownload, putar rekaman ini duluan; kalau tidak ada, baru fallback ke Jalan 3 / 2. Ini memberi rasa "kamus beneran" untuk kata-kata teratas.

---

## C. Rekomendasi Arsitektur Final (Hybrid)

1. **Kamus (teks): offline total di HP** — database SQLite dari Kaikki + WordNet. Cari kata & baca arti tidak butuh internet sama sekali.
2. **Audio kata:** (a) rekaman manusia UK bila ada & tersedia → (b) TTS bawaan HP en-GB (offline) → (c) bila online & ingin kualitas seragam terbaik: Google Cloud TTS Neural2 UK via backend cache.
3. **Audio kalimat:** selalu TTS (bawaan HP, atau Cloud bila online) — kalimat memang tidak mungkin direkam satu-satu.
4. **Cache lokal:** setiap audio dari cloud yang pernah didengar tersimpan di HP → lama-lama HP siswa punya koleksi offline sendiri untuk kata-kata yang sering ia buka.

Hasilnya: tidak bergantung 100% online, tidak melanggar ToS siapa pun, biaya mulai Rp0, UK sebagai default, dan kualitas bisa naik bertahap tanpa bongkar aplikasi.

## D. Jawaban Singkat Pertanyaan Pemilik
- Pakai Google Translate sebagai backend? **Secara teknis bisa, secara legal jangan untuk APK yang disebar.**
- Yang legal dari Google untuk itu namanya **Google Cloud Text-to-Speech** — produk berbeda, berbayar murah + kuota gratis besar, ribetnya sedang (setup sekali + backend kecil di VPS yang sudah dimiliki pemilik).
- Dan ada jalan **gratis-tidak-ribet-legal**: TTS bawaan Android di HP siswa sendiri.
