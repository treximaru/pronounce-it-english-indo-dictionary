# Rencana: arti Bahasa Indonesia ≥ 85% dari total kata

Target user (2026-10-24): arti Indonesia minimal 85% dari total kata.

## Angka
- Total kata di dataset: **91.556**
- Target 85%: **77.823 kata** ber-gloss_id
- Sekarang di database: **22.369 kata (24,4%)**
- Kekurangan: **55.454 kata**
- Catatan: isian wordlist manual (di bawah) BELUM masuk database sampai
  di-merge — jadi angka database tetap 22.369 sampai Fase E.

## Kenyataan yang mengubah rencana
Wordlist manual hanya berisi 1.121 kata tersering yang belum ada artinya.
Bahkan kalau semuanya terisi, cakupan hanya jadi 23.490 kata (25,7%).
Jadi manual saja TIDAK BISA mencapai 85% — harus ditambah sumber terbuka
lain, dan (bila perlu) MT lokal open-source untuk sisanya.

## Fase
### A. Manual — kata tersering (SEDANG BERJALAN)
Wordlist: `wordlist_gloss_prioritas.csv` (1.121 kata, urut frekuensi).
Dikerjakan Muse (BUKAN user — koreksi user 2026-10-24: "kamu yg isi loh
bukan saya"), bertahap per batch, makna umum (bukan definisi junk WordNet).
- Batch 1: SELESAI — 100 kata (rank 5–559)
- Batch 2: SELESAI — 250 kata (baris data 101–350, 'gets' s.d. "people's",
  diverifikasi: 0 kata bergeser, 0 gloss kosong, lalu di-merge)
- Batch 3: SELESAI 2026-10-24 sore — 250 kata (baris data 351–600,
  'shared' s.d. 'abandoned', diverifikasi: baris 1–600 semua terisi,
  0 gloss kosong, 0 kata bergeser; makna umum dipakai, bukan definisi
  junk WordNet — mis. 'heads' → kepala-kepala, 'faster' → lebih cepat,
  'sat' → duduk (lampau sit), 'carefully' → dengan hati-hati)
- Progres manual: 600/1.121 kata (53,5%). Batch 4 mulai dari kata 'buried'.
- Batch 4: SELESAI — 250 kata (baris data 601–850, 'buried' s.d.
  'denver', diverifikasi: 0 kata bergeser, 0 gloss kosong, 0 timpa).
  Keputusan ambigu: ate→makan, jean→denim, ought→seharusnya,
  rio→Rio, iv→IV, ai→AI, regarded→dianggap/dipandang (definisi
  vandalisme diabaikan), fuckin/pissed ditandai kasar.
- Progres manual: 1.121/1.121 kata (100%) — SELESAI 2026-10-24.
  Batch 5 (baris data 851–1.121, 'emma' s.d. 'lifted', diverifikasi:
  0 kata bergeser, 0 gloss kosong, 0 timpa) di-merge. Wordlist LENGKAP.

### B. Riset sumber terbuka (SELESAI 2026-10-24 — semua angka di bawah ini
ESTIMASI riset, wajib diukur di Fase C)
- FreeDict eng-ind: BISA, 12.785 headword, GPL (share-alike untuk data),
  tapi turunan Wiktionary → tumpang tindih tinggi, estimasi +1.500–3.000.
- Apertium eng-ind: TIDAK ADA (hanya id-ms). 0 kata. Dilewati.
- PanLex: POTENSIAL BESAR, snapshot CC0 (catat kategori lisensi per sumber
  asal), cakupan en-id belum terkuantifikasi, estimasi +10.000–30.000.
  Hanya lema; filter ketat ke kode 'ind' (bukan Malay ms/zsm).
- DBnary: BISA, CC BY-SA 3.0, edisi non-Inggris (FR/DE) berpotensi menambah
  padanan yang tidak ada di edisi Inggris, estimasi +3.000–15.000.
- ConceptNet: BISA, CC BY 4.0, estimasi +1.000–5.000, unduhan berat.
- Wikidata lexemes: CC0, kecil, +500–2.000 (opsional).
- Korpus paralel OPUS + alignment: hanya korpus berlisensi jelas (Tatoeba
  CC BY, GlobalVoices CC BY); TED (CC BY-NC-ND) dan OpenSubtitles
  (status hak cipta tak jelas) DITOLAK. Estimasi +10.000–25.000.
- DITOLAK: OmegaWiki (proyek mati), NLLB Meta (CC BY-NC), Glosbe (API
  saja), KBBI (proprietary), Google Translate (proprietary/berbayar).
- OPUS-MT en-id: BISA, Apache-2.0, ±300 MB, layak di CPU (int8 ±696
  token/detik, RAM ±516 MB). Satu-satunya sumber yang bisa menutup gap
  sendirian; dengan filter back-translation ±70–90% lolos.
- KESIMPULAN RISET: skenario tengah kamus saja ≈ 71.500 kata (≈78%) —
  di bawah 85%. Jalur realistis ke 85% = kamus (≈78%) + isi MT lolos
  filter back-translation untuk sisanya. MT harus ditandai (kolom sumber).
- Yang SUDAH habis dan tidak diulang: terjemahan id di dump Kaikki EN,
  gloss WordNet Bahasa (OMW), entri Inggris di dump Kaikki ID.

### C. Integrasi kamus — PENGUKURAN SELESAI 2026-10-24 (angka nyata)
- FreeDict (paket freedict-wikdict, CC BY-SA 3.0, 10.296 headword):
  +110 kata terukur; efektif +108 karena 2 kata ('lets', 'trans')
  sudah terisi manual batch 3 (manual didahulukan). FreeDict klasik
  ternyata TIDAK PUNYA pasangan eng-ind sama sekali.
- PanLex: 0 — tidak ada URL snapshot publik, API tidak terjangkau dari
  VM, mirror HF (1,19 GiB) hanya tabel ekspresi tanpa kolom makna.
- ConceptNet: 0 — diverifikasi dari dua dump (5.7.0 CSV 498 MB: 0 edge
  TranslationOf, 0 edge en↔id; 2020 JSON-LD 965 MB: 0 node /c/id/).
- DBnary: DILEWATI (endpoint SPARQL mati, HTTP 000) — pengukuran ulang
  SEDANG BERJALAN bersama OPUS alignment.
- Total kamus terukur: +108 kata saja (bukan estimasi ribuan).
- OPUS alignment TERUKUR 2026-10-24 (Tatoeba 12.789 + GlobalVoices
  16.043 pasangan kalimat, CC BY; Dice ≥ 0,30, cooc ≥ 2): 417 mapping,
  TAPI audit sampel ±20% noise (deprived→mengikat,
  uneducated→berpendidikan [berlawanan!], practiced→sodomi) → JANGAN
  merge buta; lewatkan filter back-translation yang sama dengan MT
  (atau review manusia untuk 33 nama). Bersih setelah buang tumpang
  tindih (49 kata sudah terisi manual batch 4 — balapan paralel,
  manual didahulukan; 10 irisan FreeDict): OPUS bersih 358 kata.
  Total kamus bersih: 466 kata (FreeDict 108 + OPUS 358).
- DBnary retry: MASIH MATI (6 metode, HTTP 000) — dilewati lagi,
  tidak ada RDF diunduh.
- PROYEKSI JUJUR (terkini): DB 22.369 + wordlist 1.121 + kamus bersih
  466 = 23.956 (26,2%) sebelum MT. Sisa untuk MT: 67.600 kata.
  MT yield jujur 33% → ±46.264 (50,5%); ±47–50% (dengan second chance
  morfologi) → ±55.700–57.800 (60,9–63,1%). Gap ke 85% pada yield 50%:
  ±20.000 kata. Dengan bar validitas tetap, 85% BELUM PASTI tercapai;
  penentu akhir: hasil MT full run + manual skala besar.
- Kata yang sudah ber-gloss tidak ditimpa.

### D. Pengisi sisa (DISETUJUI user 2026-10-24: "pakai mesin aja gpp,
yg penting valid")
MT lokal open-source (OPUS-MT en-id, jalan di CPU) untuk kata yang tidak
ter-cover kamus mana pun. Syarat validitas: (1) kamus didahulukan — MT
hanya untuk sisa; (2) filter back-translation (id→en harus kembali ke
kata asal/sinonimnya, kalau tidak dibuang); (3) penanda kualitas (kolom
sumber/flag di dataset) supaya isian MT bisa dibedakan dari isian
kamus/manual dan direview belakangan.
- VALIDASI SAMPEL SELESAI 2026-10-24 (200 kata, void, CTranslate2 int8,
  27,2 kata/detik → full run ±34 menit; model di ~/muse/mt-enid/).
  TEMUAN KUNCI: pass rate mentah menipu — strict 58,5% / loose 64,0%,
  tapi 56,5% terjemahan adalah copy-through (terjemahan = kata asal)
  dan 62 copy-through non-nama lolos strict secara palsu. Auto-accept
  jujur (loose minus copy-through non-nama) hanya 33,0% (non-nama
  19,2%). Estimasi validitas sebenarnya ±47–51% (±38–44% non-nama).
  Filter full run HARUS = loose + buang copy-through non-nama + second
  chance morfologi (bentuk turunan -ly/-ed yang back-translation-nya
  kembali ke bentuk dasar). MT DILEWATI untuk pos=name (nama dirusak:
  hayes→jerami, edith→sunting; nama tetap nama).
- IMPLIKASI 85%: dengan yield MT segitu, target bergantung penuh pada
  hasil pengukuran kamus. Bila kamus underdeliver, pilihan: terima
  ceiling di bawah 85% dengan bar validitas tetap tinggi, ATAU turunkan
  bar kualitas (tidak direkomendasikan — syarat user: "yang penting
  valid").

### E. Rilis
Merge semua ke dataset v26 (salinan v25 + gloss baru) → verifikasi
with_gloss ≥ 77.823 → repoint app → build v1.6.0-beta di void → rilis
GitHub + link unduh.

## Aturan kualitas terjemahan
- Makna umum, bukan definisi junk; singkat (1–3 padanan, pisah ';').
- Kata kerja: beri keterangan bentuk (lampau / ke-3 tunggal / sedang /
  past participle). Kontraksi = bentuk lengkapnya.
- Proper noun: pertahankan nama + keterangan singkat.
- Verifikasi per batch: jumlah terisi = target batch, kata pertama/terakhir
  batch cocok, tidak ada gloss kosong di tengah batch.

### STATUS v26 (2026-10-24 ~18:10, TERVERIFIKASI MANDIRI)
- kamus_v26.sqlite: 37.068.800 B, md5 d142f843d53713278e3f5d26cdd3e6be.
  v25 TIDAK BERUBAH (md5 e018f87b50bbb590b042022a38692745), 91.556 baris,
  0 gloss lama hilang/berubah.
- Ber-gloss: 29.050/91.556 = 31,73% (dari 24,43%; +6.681 kata).
  Per sumber: manual 1.121, freedict-wikdict 107, opus-dice-filtered 71,
  mt-opus 5.382, lama (NULL) 22.369. Masih tanpa gloss: 62.506
  (termasuk 12.161 nama yang dilewati MT).
- MT full run: 55.727 kata, lolos 5.382 (9,66% — jauh di bawah sampel 33%
  karena ekor keras: rank 6079+ dan 37 ribu kata rank-NULL termasuk token
  sampah); dibuang 50.345 (copy-through 31.074 = 55,8%; fail 19.271).
  Filter ketat juga membuang terjemahan bagus (sang→bernyanyi,
  delighted→senang, algerian→aljazair) karena back-translation meleset.
- TARGET 85% TIDAK TERCAPAI dengan bar validitas tetap (gap 48.773 kata).
  Keputusan di tangan user: rilis v1.6.0 dengan 31,73% / recovery dulu
  (lemma-family + review frequent-first atas buangan MT) / longgarkan
  filter (validitas turun). APK BELUM DI-BUILD — menunggu keputusan.
