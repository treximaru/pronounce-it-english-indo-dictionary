# STATUS — Project Kamus Pronunciation APK
**Update:** 23 Oktober 2026, sesi background (install toolchain + dataset prototype)
**Arsitektur terkunci:** kamus English–English offline (SQLite di APK Flutter) + audio TTS bawaan HP Android en-GB. Sumber terbuka: Kaikki/Wiktionary + WordNet + CMUdict.

---

## PEKERJAAN 1 — Toolchain (SEMUA di `~/workspace/tools/`, tanpa sudo, tanpa install system) ✅ SELESAI

### Yang terpasang & terverifikasi
| Komponen | Bukti konkret |
|---|---|
| Java | OpenJDK Temurin **17.0.20.1** di `~/workspace/tools/android/jre17` (sudah ada sebelumnya, dipakai sebagai JAVA_HOME) |
| Flutter SDK | **3.47.7 stable** — `flutter --version`: Framework rev `abaf9c5237` (2026-10-08), Engine `deb287481e`, **Dart 3.13.5**, DevTools 2.60.0. Di `~/workspace/tools/flutter` (2,5 GB terekstrak) |
| Arsip Flutter | `flutter_linux_3.47.7-stable.tar.xz`, 1.504 MB, dari `storage.googleapis.com/flutter_infra_release` (URL diambil dari `releases_linux.json`). **SHA256 cocok** dengan metadata rilis resmi: `af7455f540df951184c7953fbe3cf884766e7541dacf8571f9f582db03dd6230` |
| Android cmdline-tools | build **14742923** dari dl.google.com (zip 165 MB) → `~/workspace/tools/android-sdk/cmdline-tools/latest`, `sdkmanager --version` = **20.0** |
| Paket SDK (output `sdkmanager --list_installed`) | `platform-tools` **37.0.1** (adb 1.0.41 / 37.0.1-15733141) · `platforms;android-35` rev 2 · `platforms;android-36` rev 2 · `build-tools;35.0.0` · `build-tools;28.0.3` — total SDK 464 MB |
| Lisensi SDK | Diterima, 8 file di `~/workspace/tools/android-sdk/licenses/` |
| Konfigurasi Flutter | `flutter config --android-sdk ~/workspace/tools/android-sdk` sudah dijalankan |

### Hasil `flutter doctor`
- Run ke-2 (setelah SDK dilengkapi): **`[✓] Android toolchain`** — SDK terdeteksi, lisensi accepted. Network resources ✓, Proxy Configuration ✓.
- Kenapa ada android-36 + build-tools 28.0.3 padahal spek awal minta android-35/35.0.0: **doctor Flutter 3.47.7 secara eksplisit menuntut "Android SDK 36 and the Android BuildTools 28.0.3"**, jadi kedua paket itu ditambahkan di samping android-35 + build-tools 35.0.0 yang tetap terpasang.
- Isu doctor yang tersisa (tidak relevan untuk target Android): flutter/dart belum di PATH (kosmetik), Chrome tidak ada (khusus web), toolchain Linux desktop tidak lengkap (khusus desktop). Doctor run pertama sangat lambat (~20 menit) karena cek "Network resources" timeout 4,5 menit lewat proxy; run kedua selesai 6 detik.

### Kendala nyata yang ditemukan & solusinya (penting untuk sesi berikutnya)
1. **sdkmanager (Java) tidak membaca env proxy** dan koneksinya lewat proxy selalu `SocketException: Connection reset` → manifest gagal diunduh ("Failed to find package 'platform-tools'"). **Fix yang terbukti:** paksa IPv4 + proxy lokal 8899:
   ```
   export JAVA_HOME=~/workspace/tools/android/jre17
   export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true"
   sdkmanager --sdk_root=~/workspace/tools/android-sdk --proxy=http --proxy_host=127.0.0.1 --proxy_port=8899 "<paket>"
   ```
   Dengan kombinasi ini semua unduhan SDK berhasil (install 3 paket pertama selesai 52 detik).
2. Ekstrak Flutter: `tar` exit code 2 **hanya** karena peringatan "Cannot change ownership to uid 1000" untuk ribuan file (arsip membawa uid 1000, proses berjalan sebagai root). Semua file terekstrak utuh sampai akhir — dibuktikan `flutter --version` dan doctor berjalan normal.
3. **Catatan untuk tahap build APK nanti:** Java yang ada adalah **JRE** 17 (cukup untuk sdkmanager & doctor). Gradle/Kotlin saat compile APK umumnya butuh **JDK penuh (javac)** — bila build pertama gagal di titik itu, unduh Temurin JDK 17 ke `~/workspace/tools/` dengan pola yang sama.

---

## PEKERJAAN 2 — Dataset Prototype 1.000 Kata ✅ SELESAI

**Output:** `~/workspace/projects/kamus-pronunciation/data/kamus_prototype.sqlite` (276 KB)
**Script:** `~/workspace/projects/kamus-pronunciation/scripts/build_dataset.py` (bisa dijalankan ulang)
**Venv:** `~/workspace/projects/kamus-pronunciation/.venv` — nltk **3.10.4**, wordfreq **3.1.1** (ftfy 6.3.1, langcodes 3.5.1, regex, msgpack ikut terpasang)

### Jalur data yang berhasil
- Frekuensi: wordfreq `top_n_list('en', 1500)` — catatan: wordfreq 3.x mengganti nama fungsi dari `top_n_word_list` menjadi `top_n_list`; script menangani keduanya.
- Definisi + POS + contoh: NLTK WordNet. Fonem/syllable/stress: NLTK cmudict, ARPAbet→IPA dengan tabel mapping standar (AH→ʌ bila bertekanan / ə bila tidak, ER→ɝ/ɚ, dst.), stress primer ditandai ˈ dan sekunder ˌ pada IPA.
- **Blocker NLTK yang diatasi:** `nltk.download()` gagal total di VM ini — (a) SSRF guard NLTK 3.10 menolak IP 198.18.x.x (range fake-IP DNS proxy), (b) cek "non-private directory" menolak direktori group-writable. **Solusi yang dipakai:** unduh zip corpus resmi pakai curl dari `raw.githubusercontent.com/nltk/nltk_data/gh-pages` (wordnet.zip 11 MB, omw-1.4.zip 26 MB, cmudict.zip 876 KB), ekstrak ke `/tmp/kamus_nltk/corpora` + `chmod -R go-w`, jalankan dengan `NLTK_DATA=/tmp/kamus_nltk`. Zip mentahnya diarsipkan di `data/corpora_zips/` untuk pembangunan ulang tanpa unduh lagi.

### Hasil & verifikasi independen (query langsung ke SQLite)
| Metrik | Angka |
|---|---|
| Total baris | **1.000** (distinct word = 1.000, semua punya definisi EN) |
| Pemindaian pool | rank frekuensi 1–1129 dipindai untuk mendapat 1.000 valid; yang tersaring: 69 tanpa entri WordNet, 39 format non-huruf-murni (apostrof/strip), 21 terlalu pendek |
| Punya contoh kalimat | **930 / 1.000 = 93,0%** |
| Punya syllable + stress + IPA (US) | **998 / 1.000 = 99,8%** |
| `ipa_uk` | NULL di semua baris — **sengaja**, untuk pengayaan Kaikki/Wiktionary tahap berikutnya (tidak dikarang) |
| `gloss_id` | NULL di semua baris (sesuai spek prototype) |
| Rentang freq_rank tersimpan | 5 – 1129 (rank 1–4: the/to/and/of memang tidak punya entri WordNet) |
| Tabel ekstra | `words_fts` (FTS5) — pencarian teruji: MATCH 'learn' → `learn` |
| Skema `words` | id, word, pos, definition_en, example, ipa_us, ipa_uk, syllables, syllable_count, stress_index, freq_rank, gloss_id |

### Contoh baris lengkap (dari query verifikasi)
| word | pos | definition_en | example | ipa_us | syllables | count | stress | rank |
|---|---|---|---|---|---|---|---|---|
| education | noun | the activities of educating or instructing; activities that impart knowledge or skill | he received no formal education | ˌɛdʒəˈkeɪʃən | ɛ·dʒə·keɪ·ʃən | 4 | 3 | 526 |
| beautiful | adjective | delighting the senses or exciting intellectual or emotional admiration | a beautiful child | ˈbjutəfəl | bju·tə·fəl | 3 | 1 | 604 |
| important | adjective | of great significance or value | important people | ɪmˈpɔrtənt | ɪm·pɔr·tənt | 3 | 2 | 347 |
| school | noun | an educational institution | the school was founded in 1900 | ˈskul | skul | 1 | 1 | 188 |
| learn | verb | gain knowledge or skills | She learned dancing from her sister | ˈlɝn | lɝn | 1 | 1 | 698 |

Catatan jujur soal kata uji: **`pronunciation` dan `computer` TIDAK ada di dataset** — keduanya berada di luar 1.000 kata valid teratas menurut ranking wordfreq (computer baru muncul setelah rank 1129). Ini konsekuensi wajar daftar berbasis frekuensi; keduanya akan masuk saat dataset diperluas (pool diperbesar / tahap Kaikki).
Kolom `syllables` berisi pecahan suku kata **fonetis (IPA)** hasil segmentasi fonem CMU (onset-maximization), bukan pecahan ejaan — konsisten dengan kolom IPA-nya.

---

## PEKERJAAN 3 — Scaffold App Flutter + Build APK ✅ SELESAI (23 Okt 2026, ~14:28 WIB)

**Output:** `~/workspace/your_files/KamusPronunciation-prototype.apk` (48.612.397 byte / 48,6 MB, SHA256 `c49b4d50aca59043aecc377a3b88827da980479fb946a99b25b76e088751ca03`)
**App:** `~/workspace/projects/kamus-pronunciation/app/` — package `com.kamus.kamus_pronunciation`, v1.0.0 (code 1), minSdk 24, targetSdk 36, ditandatangani debug key template (cukup untuk prototype).

### Yang dibangun
- `flutter create` + dependensi `flutter_tts` ^4.2.0, `sqflite` ^2.4.1, `path` ^1.9.1 (`flutter pub get` OK, `flutter analyze` bersih).
- Dataset SQLite dibundle sebagai asset (`assets/kamus_prototype.sqlite`, 282.624 byte — ukuran identik dengan file sumber, terverifikasi di listing APK); saat run pertama disalin ke `kamus_prototype_v1.sqlite` di direktori DB aplikasi lalu dibuka read-only.
- Layar Beranda: pencarian (prefix didahulukan, lalu freq_rank) + daftar kata. Layar Detail: word, POS, IPA (US) — `ipa_uk` ditampilkan hanya bila terisi (saat ini NULL), pecahan syllables dengan syllable ber-stress ditebalkan/di-highlight, definisi EN, contoh kalimat.
- TTS: flutter_tts locale `en-GB` — tombol Listen (rate 0.5), Slow (rate 0.25), dan Listen to example (rate 0.5).

### Kendala build nyata & solusinya (penting untuk sesi berikutnya)
1. **JRE 17 tidak punya javac** → Gradle butuh JDK penuh. Diunduh **Temurin JDK 17.0.21** ke `~/workspace/tools/jdk17` (dari api.adoptium.net), `JAVA_HOME` diarahkan ke sana saat build.
2. **Gradle wrapper gagal unduh** (`SocketException: Connection reset` saat CONNECT tunnel) → fix pola sdkmanager: `JAVA_TOOL_OPTIONS=-Djava.net.preferIPv4Stack=true`.
3. **Dependensi Maven Central selalu `Read timed out`** — biang keroknya **proxy-forwarder lokal 127.0.0.1:8899**: file POM yang sama lewat proxy egress utama selesai 1,4 detik (HTTP 200), lewat 8899 timeout total 60 detik. **Fix final:** Gradle diarahkan ke proxy egress utama via `~/.gradle/gradle.properties` (systemProp http/https proxyHost/Port/User/Password diambil dari env `https_proxy` saat setup — nilainya tidak ditulis di dokumen ini) + timeout HTTP Gradle 180 detik di `android/gradle.properties`. Setelah itu build ke-4 sukses (Gradle task 1.242 detik; Gradle juga auto-install Build-Tools 36).
4. Percobaan delegasi ke subagent untuk pekerjaan ini ditolak sistem keamanan (23 Okt ~13:28) — pekerjaan akhirnya dikerjakan langsung di sesi utama dan berhasil. Percobaan build gagal total 3×, semuanya murni jaringan/proxy, bukan kode (analyze bersih sebelum build pertama).

### Langkah berikutnya
1. Uji instal di HP pemilik (Redmi Note 11): cek TTS en-GB device (kualitas suara penentu), pencarian, dan tombol Slow.
2. Pengayaan `ipa_uk` + `gloss_id` dari Kaikki/Wiktionary; perluas dataset ke 100 rb+ kata (saat itu `pronunciation`, `computer` dst. ikut masuk) — ganti nama file DB versi (`_v2`) agar tidak tertutup salinan lama.
3. Signing release proper (keystore sendiri) bila prototype naik jadi rilis beneran.

---

## PEKERJAAN 4 — Dataset v2 (Kaikki) + Rebrand + APK v2 ✅ SELESAI (23 Okt 2026, ~16:16 WIB)

**Output:** `~/workspace/your_files/PronounceIt-v2-arm64.apk` (32.452.932 byte / 32,5 MB, SHA256 `9c29abad0bfe919ebfef101eec9b3cd754c541f677a4299874199690eb42d996`), label terverifikasi via aapt: **"English Dictionary: Pronounce It!"** (nama pilihan pemilik, menggantikan "Kamus Pronunciation"), package sama `com.kamus.kamus_pronunciation` (instal sebagai update di atas v1), asset terbundle `assets/kamus_v2.sqlite` 33.067.008 byte (identik file sumber), tanda tangan valid.

### Dataset v2 (`data/kamus_v2.sqlite`, 33 MB, skrip `scripts/enrich_kaikki.py`)
- Sumber: `data/kaikki-en.jsonl` (dump wiktextract English Wiktionary via kaikki.org, 3.430.807.113 byte, Last-Modified 21 Okt 2026; CC BY-SA) di-stream ke staging disk (RAM datar), lalu digabung.
- Hasil: **91.556 kata** (1.000 prototype + 90.556 baru). Cakupan: IPA UK/RP bertanda khusus 36.725 (40,1%), IPA US 53.949, `ipa_other` 54.335, minimal-satu-IPA **100%**, syllables (CMU) 33.369, contoh 61.138, gloss_id 10.916 (11,9%). Statistik: `data/dataset_v2_stats.json`.
- Kolom baru **`ipa_other`**: transkripsi Wiktionary TANPA label wilayah. Temuan penting: banyak headword (termasuk *pronunciation* sendiri) hanya punya IPA tanpa tag UK/US — run pertama membuangnya sehingga *pronunciation* hilang; run kedua menyimpannya sebagai `ipa_other` dan app menampilkannya tanpa label (tidak pernah dilabeli UK/US secara karangan). Klasifikasi tag kini token-based (substring lama berisiko: "Australia" mengandung "us").
- App: IPA ditampilkan UK dulu → US → tanpa label; baris "Arti: …" bila gloss_id ada; DB disalin ke nama file baru `kamus_v2.sqlite` agar tidak tertutup salinan v1.

### Catatan pengiriman
- Lampiran chat untuk file besar TERPOTONG di sisi HP pemilik (v1 48,6 MB gagal; arm64 17 MB tiba 13 MB). Jalur yang terbukti: link unduh langsung Muse storage + sebutkan ukuran byte persis untuk verifikasi. APK v1 akhirnya terinstal baik via link ("sudah bagus" — pemilik, 23 Okt).


## PEKERJAAN 6 — Koreksi user + gloss WordNet Bahasa + APK v2.2 (2026-10-23 16:31–17:01 WIB)

Koreksi user atas v2: (1) IPA UK/US masih bercampur & default kadang ketuker; (2) tambahkan arti Indonesia sebelum definisi; (3) tombol clear pencarian (bukan hapus manual); (4) About: selain nama user, tambahkan "proudly present for the four pillars English club of Panca Bhakti Vocational High school".

Perubahan app (v1.1.0/v2.1, lalu digabung ke v1.2.0/v2.2 sebelum v2.1 sempat dikirim):
- IPA: SATU transkripsi utama saja, rantai prioritas ipa_uk -> ipa_other -> ipa_us (label IPA (UK) / IPA / IPA (US)); berlaku di detail & subtitle daftar. US tidak lagi jadi default diam-diam.
- Section "Arti (Bahasa Indonesia)" tampil sebelum "Definition" bila gloss ada.
- Kolom pencarian: suffixIcon tombol ✕ (clear) muncul saat ada teks.
- Halaman About baru (ikon info di AppBar): nama app, versi, "Developed by Muhammad Abdul Aziz, S.Pd", kalimat "Proudly presented for the Four Pillars English Club of Panca Bhakti Vocational High School", atribusi sumber terbuka.

Gloss — dua jalur dicoba:
- id.wiktionary via Kaikki (kaikki-id.jsonl 70.005.729 B, dump 21 Okt 2026): GAGAL TOTAL — isinya 40.742 entri HANYA headword bahasa Indonesia (lang 'id'), nol headword Inggris, nol translations ke 'en'. scripts/merge_gloss_id.py mengisi 0. Jalur ini buntu.
- WordNet Bahasa (Open Multilingual Wordnet omw-1.4, wn-data-ind.tab di msa/, header menyatakan MIT, http://wn-msa.sourceforge.net/; 38.085 synset ber-lemma Indonesia): scripts/merge_gloss_wordnet_bahasa.py — aturan kualitas: synset Inggris pertama yang lemma-nya memuat kata persis (case-sensitive; membuang sampah singkatan/nama diri: was->Washington, at->astatine) DAN punya lemma Indonesia; gloss = maks 3 lemma. Hasil: +11.453 kata -> gloss_id 10.916 -> 22.369 / 91.556 = 24,4%. Probe bersih: democracy->demokrasi, freedom->kebebasan, government->pemerintah, just->adil, benar, berpatutan. Output data/kamus_v22.sqlite (33.861.632 B).

APK FINAL v2.2: ~/workspace/your_files/PronounceIt-v22-arm64.apk = 32.738.461 B, SHA256 7c5cf5aafb67244187d73f8cd7cdd4c8aef97703d180537f7c96cea9aafa6c60, versionName 1.2.0 (code 2003), label "English Dictionary: Pronounce It!", asset dalam APK = kamus_v22.sqlite persis 33.861.632 B, package sama (update di atas v2). Link Muse storage: https://muse.ai/files/1397741110080420/1413954850893433/va1b6hprccxecsrh0kd6pxw6/PronounceIt-v22-arm64.apk (kedaluwarsa 2026-10-25 17:01 WIB). Catatan: build v2.1 (1.1.0, 32.453.201 B, SHA 2d13d381...) selesai 16:46 tapi TIDAK dikirim — digantikan v2.2 sesuai pilihan user "gabungkan sekalian". Build v2.1 makan 12,2 menit, v2.2 cuma 2,2 menit (cache Gradle hangat).


## PEKERJAAN 7 — Polish v2.3: keyboard autofocus, versi beta, About reorder (2026-10-23 17:09–17:38 WIB)

Koreksi user atas v2.2: (1) keyboard otomatis — muncul saat app dibuka, saat kembali dari halaman detail, dan setelah clear ("keyboard centik"); (2) versi ditambah "- beta"; (3) judul "Pronounce It!" di header ditebalkan; (4) "Developed by" dipindah ke paling bawah About; (5) tulisan Four Pillars dibuat bold italic.

Implementasi: FocusNode di _HomePageState + autofocus:true di TextField pencarian; requestFocus() di handler tombol clear dan di .then() setelah Navigator.push detail kembali (guard mounted); AppBar title TextStyle bold; About diurut ulang (nama app -> versi "1.2.0 - beta" -> Four Pillars bold italic -> Data sources -> Developed by di dasar); pubspec version 1.2.0-beta+4 (aapt versionName terverifikasi '1.2.0-beta'). Dataset TIDAK berubah (asset tetap kamus_v22.sqlite, nama file lokal sama, jadi update mulus).

APK v2.3: ~/workspace/your_files/PronounceIt-v23-arm64.apk = 32.738.469 B, SHA256 092862f39381e131d864f2dff8417434759131c2d09c899087d56b9b4bc6c344, versionCode 2004. Upload pertama terputus restart layanan (file lokal diverifikasi utuh via SHA), upload ulang sukses: https://muse.ai/files/1397741110080420/1953682172274837/k3fi0cgj2s8q69cmnbz1rs5g/PronounceIt-v23-arm64.apk (kedaluwarsa 2026-10-25 17:38 WIB).


## PEKERJAAN 8 — Dokumentasi + repo git lokal untuk persiapan GitHub (2026-10-23 ~17:45 WIB)

Atas permintaan user ("buat dokumentasinya dulu, untuk persiapan upload ke github biar tidak hilang"):
- README.md utama (Inggris, GitHub-facing) di root proyek: deskripsi, fitur, tabel sumber data + lisensi, pipeline dataset (3 skrip + URL dump), cara build dari sumber, struktur proyek, riwayat versi, roadmap, kredit (Four Pillars + Developed by).
- .gitignore root: .venv, data/*.jsonl (dump 3,2 GB), data/*.sqlite, corpora_zips, build Flutter, app/assets/kamus_v22.sqlite, *.apk/*.aab (binari via GitHub Releases).
- docs/: 3 dokumen konsep disalin dari your_files (Konsep, Pembaruan v1.1, Spek Prototype).
- git init -b main + commit awal 14d7a14: 142 file terlacak, file terbesar cuma 104K (ikon) — bersih dari file raksasa. Identitas repo-lokal: "Muhammad Abdul Aziz <aziz@localhost>" (email placeholder, ganti ke email GitHub sebelum push).
- BELUM di-upload ke GitHub — menunggu user (buat repo + remote + push, atau minta Muse bantu saat akun siap). APK didistribusikan via Releases, bukan commit.


## PEKERJAAN 9 — Fix keyboard pertama buka + jeda GitHub (2026-10-23 17:52–18:22 WIB)

User menunda upload GitHub ("nanti dulu") karena bug: saat PERTAMA kali buka app, keyboard tetap tidak muncul meski sudah autofocus di v2.3. Proses gh auth login (kode D119-8170) dihentikan atas jeda ini; repo akan dibuat PUBLIC sesuai pilihan user, nama pronounce-it-english-indo-dictionary, email git sudah treximaru@gmail.com (commit lokal diamend ke 076b0d2).

Penyebab: autofocus:true tidak andal pada peluncuran pertama — field selesai dibangun sebelum window mendapat fokus, permintaan keyboard hilang. Fix v2.4 (1.2.0-beta+5): _HomePageState.initState meminta fokus via WidgetsBinding.addPostFrameCallback -> _focusNode.requestFocus(); jalur kembali-dari-detail juga dibungkus post-frame callback yang sama. flutter analyze bersih.

APK v2.4: ~/workspace/your_files/PronounceIt-v24-arm64.apk = 32.738.469 B, SHA256 d24872b26750a1c17c07f7d69ff244331d70b812f05ba4d32e50c021c5907c5c, versionCode 2005, versionName '1.2.0-beta', asset kamus_v22.sqlite utuh. Link: https://muse.ai/files/1397741110080420/1096072899880846/m826ikpmo0y73ekin0wicjwh/PronounceIt-v24-arm64.apk (kedaluwarsa 2026-10-25 18:22 WIB). Fix juga di-commit ke repo lokal (setelah commit awal 076b0d2). Menunggu tes user pada skenario buka-pertama; GitHub push menyusul setelah app dinyatakan beres.


## PEKERJAAN 10 — Keyboard masih gagal di v2.4 -> serangan 3 lapis v2.5 (2026-10-23 18:25–18:38 WIB)

User melaporkan v2.4 TETAP tidak memunculkan keyboard saat start. Diagnosis: MIUI/Redmi mengabaikan permintaan keyboard implisit saat peluncuran; post-frame requestFocus saja tidak cukup. Fix v2.5 (1.2.0-beta+6), tiga lapis sekaligus:
1. AndroidManifest: windowSoftInputMode "adjustResize" -> "stateAlwaysVisible|adjustResize".
2. MainActivity.kt (sebelumnya kosong): override onWindowFocusChanged -> Handler postDelayed 400 ms -> InputMethodManager.showSoftInput(decorView, SHOW_FORCED).
3. Dart initState: post-frame requestFocus + retry Future.delayed 450 ms bila belum fokus.
flutter analyze bersih; build sukses 2,6 menit (Kotlin terkompilasi).

APK v2.5: ~/workspace/your_files/PronounceIt-v25-arm64.apk = 32.738.469 B, SHA256 814f5c4fc1c11a24fa16667e959b6968abc8b43b9d62444f2181f16789bfc50b, versionCode 2006. Link: https://muse.ai/files/1397741110080420/1874862387289016/rvglgtf2jcma9y09ew1i5uri/PronounceIt-v25-arm64.apk (kedaluwarsa 2026-10-25 18:38 WIB). Fix di-commit lokal. Diagnostik cadangan bila masih gagal: tanya user apakah kursor berkedip di kolom pencarian (fokus dapat tapi IME diblokir vs fokus gagal total).


## PEKERJAAN 11 — v2.5 gagal juga; diagnosis kursor -> retry-loop native v2.6 (2026-10-23 18:44–18:52 WIB)

User melaporkan v2.5 tetap gagal DAN memberi data kunci: "kursor berkedip" — fokus Dart PASTI mendarat; yang dibuang MIUI adalah panggilan showSoftInput-nya (kemungkinan: target decorView bukan view input yang benar, dan/atau panggilan tunggal 400 ms jatuh sebelum koneksi text-input Flutter siap saat cold start).

Fix v2.6 (1.2.0-beta+7): MainActivity.kt ditulis ulang jadi retry-loop — saat window focus: tiap 300 ms (maks 10x) panggil imm.showSoftInput(decorView.findFocus() ?: decorView, 0), berhenti begitu rootWindowInsets.isVisible(IME) == true. Manifest stateAlwaysVisible + retry Dart dipertahankan. Analyze bersih, build 1,7 menit.

APK v2.6: ~/workspace/your_files/PronounceIt-v26-arm64.apk = 32.738.469 B, SHA256 17c4568c0b2809b9d2662b730d7f1a85afaff56772333a91f9e4f2c570ecce67, versionCode 2007. Link: https://muse.ai/files/1397741110080420/1755840639043990/zu32kq5q9sl8ktuazgfmjwg4/PronounceIt-v26-arm64.apk (kedaluwarsa 2026-10-25 18:52 WIB). Di-commit lokal. Menunggu tes user.


## PEKERJAAN 12 — Keyboard v2.6 TERKONFIRMASI + lanjut GitHub (2026-10-23 ~19:12 WIB)

User mengonfirmasi v2.6: "Oke udah muncul sekarang" — keyboard muncul saat start. Saga keyboard selesai: yang berhasil = retry-loop native showSoftInput ke view fokus sampai IME terlihat (v2.6), di atas fondasi stateAlwaysVisible + fokus Dart. v2.3/v2.4/v2.5 gagal di MIUI.

User memerintahkan lanjut persiapan GitHub. Alur gh auth login --web diulang (kode lama mati karena proses dihentikan): kode device baru diterbitkan, menunggu persetujuan user; setelah itu buat repo PUBLIC pronounce-it-english-indo-dictionary + push + Release v1.2.0-beta berisi APK v2.6.


## PEKERJAAN 13 — TERBIT DI GITHUB (2026-10-23 ~19:18–19:19 WIB)

gh auth login berhasil (akun treximaru, device code F7D4-BDD5 disetujui user). Repo PUBLIC dibuat + push sukses: https://github.com/treximaru/pronounce-it-english-indo-dictionary (branch main -> origin/main, semua commit sampai d84285c). Release pre-release v1.2.0-beta dibuat dengan PronounceIt-v26-arm64.apk terlampir: https://github.com/treximaru/pronounce-it-english-indo-dictionary/releases/tag/v1.2.0-beta. Proyek resmi terarsip di GitHub — tujuan "biar tidak hilang" tercapai. gh di VM kini terautentikasi sebagai treximaru (token di ~/.config/gh, JANGAN dicetak).

## PEKERJAAN 14 — SELESAI (dataset + kode) / BUILD TERBLOKIR ENV (2026-10-24 ~05:00-05:50)
- Fitur sinonim & antonim (permintaan owner): dataset kamus_v23.sqlite (36.573.184 B) = v22 + kolom synonyms/antonyms. Sumber: Wiktionary (Kaikki, per-makna) utama + WordNet pengisi; dibersihkan (hanya kata yang juga headword; buang nama diri). Hasil akhir: sinonim 33.056 kata (36,1
## PEKERJAAN 14 — SELESAI (dataset + kode) / BUILD TERBLOKIR ENV (2026-10-24 ~05:00-05:50)
- Fitur sinonim & antonim (permintaan owner): dataset kamus_v23.sqlite (36.573.184 B) = v22 + kolom synonyms/antonyms. Sumber: Wiktionary (Kaikki, per-makna) utama + WordNet pengisi; dibersihkan (hanya kata yang juga headword; buang nama diri). Hasil akhir: sinonim 33.056 kata (36,1%), antonim 7.993 kata (8,7%). Script: scripts/add_synonyms_antonyms.py.
- App v1.3.0-beta+8: section Synonyms (chip HIJAU) & Antonyms (chip MERAH) setelah Example; chip bisa diketuk -> lompat ke halaman kata tsb (KamusDb.lookup). About: "Version 1.3.0 - beta · October 2026" (bulan-tahun di sebelah versi, sesuai permintaan owner) + atribusi sumber diperbarui. flutter analyze BERSIH.
- BUILD GAGAL TOTAL di instance VM ini: sejak restart ~05:05, Gradle daemon tidak pernah bisa dihubungi client ("could not be connected" / "first result empty") — bahkan ./gradlew help gagal/hang. Diagnosis: loopback TCP biasa normal (tes python http.server 200), JVM polos pegang 800MB RAM normal, daemon hidup sehat tapi handshake client<->daemon black-hole; daemon single-use berhenti sendiri setelah idleTimeout 120s. RAM host juga tertekan (MemAvailable ~0,6-0,9GB dari 8GB; AnonPages lokal cuma 1,26GB -> tekanan dari luar instance). Semua build semalam (s/d v2.6) jalan di instance SEBELUM restart. Kesimpulan: cacat environment instance ini, BUKAN kode/dataset. Opsi: build di batam (SSH publik terverifikasi) atau tunggu instance VM berganti/pulih lalu build ulang.

## PEKERJAAN 15 — SELESAI (2026-10-24 ~05:57): Britfone tambal stress & suku kata (dataset v2.4)
- Owner memilih opsi "Pakai Britfone untuk tambal stress & suku kata". File britfone.main.3.0.1.csv (433.285 B, MIT) diunduh ke data/.
- Script scripts/merge_britfone_stress.py: parse 15.169 entri Britfone -> fonem + posisi stress primer; silabifikasi aturan onset-legal (keluarga yang sama dgn CMU syllabify v2) + konsonan silabis akhir kata; stress_index 1-based sesuai format lama; ISI HANYA baris NULL, tidak menimpa data lama.
- Hasil terukur JUJUR: terisi 361 kata saja -> cakupan suku kata/stress 33.730/91.556 (36,8%, naik 0,4pp). Sebabnya struktural: 58.187 kata tanpa suku kata mayoritas kata langka/long-tail Wiktionary, sedangkan Britfone memang daftar top-frequency (hampir semua isinya sudah ter-cover CMU). Nilai unik Britfone terkonfirmasi: ejaan British (favourite, honour, neighbourhood) + kata modern (google, twitter, podcast, upload, anime, remix) — titik buta CMU (Amerika). Contoh isi benar: google guː·gəl (1), upload ɐ·pləʊd (1), mumbai mʊm·baɪ (2).
- Dataset kamus_v24.sqlite (36.585.472 B); app diarahkan ke v24 (KamusDb + pubspec + aset). ipa-dict TIDAK dipakai (sesuai evaluasi: en_UK turunan GPL-3.0 + tumpang tindih Kaikki).
- Build APK v1.3.0 masih terblokir env VM (Gradle) — menunggu keputusan owner: build di batam vs tunggu instance pulih.

## PEKERJAAN 16 — Build v1.3.0 di void + rilis (2026-10-24)
- Toolchain void (~/muse/tools/): JDK Temurin 17.0.21, Android SDK (platform 36, build-tools 35.0.0 + 36.0.0 auto-install AGP, platform-tools, cmdline-tools, NDK 28.2.13676358), Flutter 3.47.7. Dua bug installer diperbaiki (urutan rakit chunk paralel; parser repository XML) + dua seed paralel (Gradle 9.3.1-all, NDK r28c) karena unduhan satu aliran di void kena throttle ±46 KB/s.
- Build release arm64 SUKSES: PronounceIt-v27-arm64.apk, 33.540.033 B, md5 2453f0b09f1aebf7ec437c6c6f203f84, SHA256 98abc6b622293bc71ff913d3652fde9e377ee6cc12c4a66e43b21cc73264aa50. versionName 1.3.0-beta (code 8); DB terbundel md5 ecd058b9… identik kamus_v24.
- GitHub pre-release v1.3.0-beta terbit dengan APK terlampir.

## PEKERJAAN 17 — Keystore rilis tetap + fix urutan search + rebuild (2026-10-24)
- Laporan owner: (1) synonyms/antonyms tidak ketemu & About tanpa bulan/tahun — akar masalah: APK v27 pertama ditandatangani debug key void (SHA-256 6ef22447…) ≠ debug key VM build v26 (6ad2b297…) → Android menolak update di atas instalasi lama, yang jalan di HP owner masih v1.2.0. (2) Kata persis hasil search muncul di bawah — akar masalah: 37.038/91.556 kata freq_rank NULL dan SQLite menaruh NULL paling depan saat ASC (bukti: 'read' ke-4 di bawah 'read out'/'read receipt'/'readaway').
- Keystore rilis TETAP dibuat: pronounce-it-release.jks, alias pronounceit, RSA 2048, berlaku 24 Okt 2026 – 16 Okt 2056, cert SHA-256 ecb11ce59d18665d30ed54c35b1512e7c56800a596a450aacc203a202584af8a. Master di signing/ (0600, git-ignored) + password.txt di sebelahnya; salinan di void ~/muse/pronounce-it-signing/. build.gradle.kts: signingConfigs.release dari key.properties (git-ignored), fallback debug bila file tidak ada. Verifikasi signingReport di void: SHA-256 cocok.
- Fix search (commit 179768e): ORDER BY (LOWER(word) = ?) DESC, prefix DESC, (freq_rank IS NULL) ASC, freq_rank ASC, word ASC; daftar awal juga nulls-last. Dites di dataset asli (read/sing/fast: kata persis teratas), flutter analyze bersih.
- Rebuild di void (HEAD 179768e) SUKSES: APK 33.540.033 B, md5 e0a4d273f72368f3da148237966b645f, ditandatangani keystore tetap (apksigner: ecb11ce5… ✓), DB terbundel ecd058b9… ✓, string fix ada di libapp.so ✓. Aset GitHub release v1.3.0-beta DIGANTI (--clobber) + catatan rilis ditambah penjelasan. Owner: uninstall sekali ini saja (terakhir), setelah itu update selalu langsung terpasang.

## PEKERJAAN 18 — Tema Terang/Gelap/Ikuti sistem, v1.4.0-beta (2026-10-24)
- Permintaan owner: tema gelap/terang/ikuti sistem. Implementasi (commit 4f502f8): ValueNotifier<ThemeMode> global + SharedPreferences (kunci theme_mode) sehingga pilihan tersimpan antar-restart; MaterialApp theme (indigo seed) + darkTheme (seed sama, brightness dark) + themeMode; tombol ikon di AppBar beranda yang berputar System -> Light -> Dark (ikon brightness_auto/light_mode/dark_mode). Perbaikan dark-safe: baris suku kata tidak lagi pakai Colors.black87 (warisi warna teks tema), header & chip Synonyms/Antonyms pakai shade terang di mode gelap.
- Build di void: plugin baru shared_preferences_android menarik compileSdk 35 → sdkmanager mengunduh satu-kali Android SDK Platform 35 (142 MB terurai) + CMake 3.22.1; keduanya kini permanen di toolchain void. (Alur unduhan satu-aliran void ~110 KB/s; total build lebih lama dari biasanya.)
- APK v1.4.0-beta+9 SUKSES & terverifikasi: 34.552.229 B, md5 eb2fce5ed916e9c7352210f56053d17f, versionCode 9, ditandatangani keystore tetap (ecb11ce5… ✓ — terpasang langsung di atas v1.3.0 bertanda tangan, TANPA uninstall), DB terbundel ecd058b9… ✓, string theme_mode ada di libapp.so ✓.
- GitHub pre-release v1.4.0-beta dibuat dengan APK terlampir; link storage kedaluwarsa 2026-10-26 13:46 WIB.

## PEKERJAAN 19 (2026-10-24 sore — dataset v25: filter contoh kuno + definisi kata fungsi)
- Permintaan user: (1) saring contoh kuno di dataset berikutnya (contoh 'and' = kutipan resep Middle English c. 1430), (2) perbaiki definisi kata fungsi yang rancu (a=angstrom, was=Washington, at=astatin, does=Dept. of Energy), (3) wordlist manual diteruskan pelan-pelan.
- Skrip: scripts/build_v25.py (reproducible; v24 TIDAK diubah, v25 = salinan + perbaikan). Laporan: scripts/v25_report.txt.
- Temuan ukur: dari 61.138 contoh di DB, 6.777 terdeteksi kuno (ref tahun < 1700 ATAU penanda Middle English þ/ð/thou/hath/doth) → 4.361 diganti contoh modern dari entri kata yang sama (pos sama diutamakan), 2.416 dipertahankan karena tidak ada contoh modern di entri kata itu (lebih baik daripada contoh sense yang salah). Contoh: 'and' kini "as for Mrs. Smith, she had claims of various kinds to recommend her quickly and permanently."
- Definisi: 56 kata fungsi diganti pos + definisi ke makna umum (a/an/are/as/at/be/can/do/does/did/doing/have/has/had/having/he/i/in/it/its/may/me/might/must/no/of/on/or/over/so/us/was/while/who/will/am/is/were/been/made/got/should/about/above/after/before/below/between/through/under/with/within/without/for/by/but). Wordlist ikut diperbaiki (19 baris).
- Build v29 / v1.5.0-beta+10 di void (build_v13f.log, BUILD_EXIT=0): badging versionCode 10 / 1.5.0-beta, sertifikat = keystore permanen ecb11ce5… (install langsung di atas v1.4.0, tanpa uninstall), DB bundle md5 = v25 (e018f87b…), isi APK terverifikasi ('and' contoh modern, 'was' = verb Past tense of be). APK 34.595.485 B, md5 700f51ecd67e788b19e89d81cbd06291. GitHub pre-release v1.5.0-beta live.
- INSIDEN PROSES: /tmp di VM ini adalah tmpfs 512 MB — file grep dump gloss (433 MB) + v25 (70 MB) membuatnya 100% penuh dan membunuh skrip dua kali (pesan "No space left on device"; gejala awal: log kosong + exit 1 tanpa traceback). Perbaikan: hapus file /tmp tadi, temp skrip dipindah ke ~/workspace/tmp/v25 (disk). PELAJARAN: jangan tulis intermediate besar ke /tmp di VM ini.
- Transfer aset batam→void lambat (~40–60 KB/s, 36 MB ≈ 11 menit); arah void→batam cepat (~30 dtk). Sesi SSH luar sempat menggantung setelah build jalan (nohup di void tetap jalan) — sesi dibunuh, build dipantau lewat log.
- Wordlist manual: tetap jalur pelan-pelan (1.121 kata, gloss_id kosong, definisi sudah tidak menyesatkan). Belum ada isian terjemahan → v25 belum menambah gloss (tetap 22.369).
