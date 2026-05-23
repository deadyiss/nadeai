# Demo — RAG System dengan Deteksi Konflik & Halusinasi

Dokumen ini berisi panduan lengkap untuk melakukan demo sistem, termasuk skenario dokumen, pertanyaan, dan interpretasi output yang diharapkan.

---

## Persiapan Demo

### 1. Jalankan Aplikasi

```bash
cd /home/deadyiss/Downloads/tugas-ai
source venv/bin/activate
python3 app.py
```

Tunggu hingga muncul:
```
Bootstrap complete.
 * Running on http://127.0.0.1:5000
```

Buka browser: `http://localhost:5000`
Login: `admin` / `admin123`

---

### 2. Upload Dokumen Demo

Buat dan upload 7 dokumen berikut via halaman web (drag & drop ke upload zone, centang **Shared**).

> Semua dokumen membahas perusahaan fiktif **PT Teknologi Maju Indonesia** dengan data yang sengaja saling bertentangan antar divisi.

---

## Dokumen Demo

### Dokumen 1 — `laporan_keuangan_2024.docx`

```
LAPORAN KEUANGAN TAHUNAN 2024
PT Teknologi Maju Indonesia
Divisi: Keuangan & Akuntansi | Tanggal: 31 Desember 2024

Total pendapatan 2024: Rp 48 miliar
Laba bersih 2024: Rp 12 miliar
Jumlah karyawan: 340 orang (rata-rata gaji Rp 64,7 juta/tahun)
Kantor: Jakarta, Surabaya, Bandung (3 kantor)
Total aset: Rp 95 miliar (gedung Jakarta: Rp 40 miliar)
Produk: DataSync Pro versi 4.2 (diluncurkan Agustus 2024)
Pengguna aktif DataSync Pro: 12.500 perusahaan
Harga langganan Enterprise: Rp 5 juta/bulan
Target 2025: pendapatan Rp 60 miliar, rekrut 80 karyawan baru
Ekspansi: buka kantor Medan dan Makassar
```

---

### Dokumen 2 — `laporan_hrd_2024.docx`

```
LAPORAN SUMBER DAYA MANUSIA 2024
PT Teknologi Maju Indonesia
Divisi: Human Resources | Tanggal: 15 Januari 2025

Total karyawan aktif: 312 orang (bukan 340 seperti diklaim keuangan)
Rincian: 180 engineer, 65 sales, 42 operasional, 25 manajerial
Turnover rate 2024: 8,2% (28 orang resign, 45 orang masuk)
Gaji rata-rata: Rp 8,5 juta/bulan (total kompensasi Rp 9,2 juta/bulan)
Total pengeluaran gaji 2024: Rp 25 miliar (keuangan sebut Rp 22 miliar)
Kantor aktif: Jakarta dan Surabaya (Bandung tutup Maret 2024)
Budget pelatihan: Rp 1,2 miliar, 18.500 jam pelatihan, 156 sertifikat
Target rekrutmen 2025: 60 orang (bukan 80 seperti diklaim keuangan)
Fokus: 40 backend engineer, 15 data scientist, 5 product manager
```

---

### Dokumen 3 — `laporan_produk_datasync.docx`

```
LAPORAN PRODUK DATASYNC PRO
PT Teknologi Maju Indonesia
Divisi: Product & Engineering | Tanggal: 20 Januari 2025

Versi terkini: DataSync Pro 4.3 (bukan 4.2 — dirilis 10 November 2024)
Riwayat: v4.0 (5 Jan 2023), v4.2 (15 Ags 2024), v4.3 (10 Nov 2024)
Pengguna berbayar aktif: 9.800 perusahaan
Pengguna trial (belum bayar): 2.700 perusahaan
Total semua user: 12.500 (angka yang diklaim laporan keuangan)
Harga Starter: Rp 1,5 juta/bulan
Harga Professional: Rp 3 juta/bulan
Harga Enterprise: Rp 5 juta/bulan
Roadmap: versi 5.0 rencana rilis Q2 2025 (April-Juni)
Target akhir 2025: 15.000 pelanggan berbayar
```

---

### Dokumen 4 — `notulen_rapat_direksi_jan2025.docx`

```
NOTULEN RAPAT DIREKSI
PT Teknologi Maju Indonesia
Tanggal: 10 Januari 2025 | Lokasi: Kantor Pusat Jakarta
Peserta: CEO (Andi Wijaya), CFO (Sri Mulyani), CTO (Budi Hartono),
         COO (Dewi Santoso), VP Sales (Reza Akbar)

KEPUTUSAN:
- Jumlah karyawan resmi: 312 orang (mengikuti data HRD, bukan keuangan)
- Laba bersih 2024 (setelah koreksi pajak Rp 1,5 miliar): Rp 10,5 miliar
- Versi produk terkini dikonfirmasi: DataSync Pro 4.3
- Pengguna berbayar aktif: 9.800 perusahaan
- Target rekrutmen 2025: 60 orang
- Ekspansi hanya ke Medan (bukan Medan + Makassar), target Q3 2025
- Anggaran ekspansi: Rp 3,5 miliar
- Total anggaran operasional 2025: Rp 42 miliar
- Alokasi R&D 2025: Rp 9 miliar (naik dari Rp 6 miliar)
- Versi 5.0: target Q2 2025, buffer hingga Q3 jika ada kendala teknis
```

---

### Dokumen 5 — `audit_eksternal_2024.docx`

```
LAPORAN AUDIT EKSTERNAL
PT Teknologi Maju Indonesia
Auditor: KAP Santoso & Rekan | Tanggal: 25 Januari 2025

TEMUAN:
1. Pendapatan aktual per PSAK 72: Rp 45,7 miliar (selisih Rp 2,3 miliar dari laporan)
2. Laba bersih setelah audit: Rp 9,8 miliar
   (keuangan: Rp 12M → direksi koreksi: Rp 10,5M → audit: Rp 9,8M)
3. Karyawan terverifikasi dari daftar gaji: 318 orang
   (termasuk 6 karyawan kontrak yang tidak tercatat HRD)
4. Aset gedung Jakarta revaluasi: Rp 35 miliar (bukan Rp 40 miliar)
   Total aset terkoreksi: Rp 90 miliar (laporan: Rp 95 miliar)
5. Pengguna berbayar ≥3 bulan berturut-turut: 8.900 perusahaan
   Pengguna yang bayar minimal 1 kali: 10.200 perusahaan
6. Kantor aktif: Jakarta (penuh) + Surabaya (40% kapasitas)

OPINI: Wajar Dengan Pengecualian (WDP) atas isu PSAK 72
```

---

### Dokumen 6 — `laporan_sales_q4_2024.docx`

```
LAPORAN SALES & MARKETING Q4 2024
PT Teknologi Maju Indonesia
Periode: Oktober - Desember 2024

Kontrak baru Q4: 87 perusahaan (nilai: Rp 5,2 miliar)
Total pelanggan (berbayar + trial): 12.500
Berbayar: 9.800 | Trial: 2.700
Churn rate Q4: 2,1% (kehilangan 210 pelanggan)
Tim sales: 35 orang, target 5 kontrak/orang, pencapaian 2,5 kontrak (50%)
Sales terbaik: Ahmad Fauzi (12 kontrak, Rp 720 juta)
Pipeline Q1 2025: 450 prospek, estimasi konversi 30% (~135 pelanggan baru)
Kompetitor: Sinkron.id (Rp 2 juta/bulan, tumbuh 40% YoY)
Kehilangan 3 enterprise client besar ke Sinkron.id
```

---

### Dokumen 7 — `rencana_teknologi_2025.docx`

```
RENCANA PENGEMBANGAN TEKNOLOGI 2025
PT Teknologi Maju Indonesia
Divisi: Engineering & CTO Office | Tanggal: 8 Januari 2025

Roadmap:
- v4.3 (sudah rilis Nov 2024): stabil, minor bug fixes
- v4.4 (rencana Feb 2025): +50 konektor baru
- v5.0 (rencana Juni 2025): natural language query, AI assistant
- Buffer v5.0: bisa mundur hingga September 2025

Infrastruktur: AWS Singapore (utama) + GCP Taiwan (backup)
Cloud cost 2024: Rp 850 juta/bulan | Target 2025: Rp 700 juta/bulan

Tim engineering: 180 orang
Backend: 95 | Frontend: 45 | DevOps: 20 | QA: 20
Rekrutmen teknis 2025: 40 backend + 15 data scientist = 55 orang
(catatan: rekrutmen teknis saja sudah 55 dari total target 60 orang HRD)

Bug backlog: 847 isu (237 critical, 410 medium, 200 low)
Target sebelum v5.0: kurangi critical bugs ke <50

Ancaman: Sinkron.id agresif di segmen mid-market, tumbuh 40% YoY
```

---

## 10 Pertanyaan Demo & Output yang Diharapkan

---

### 1. Berapa jumlah karyawan PT Teknologi Maju Indonesia saat ini?

**Jawaban yang diharapkan:** 312 orang (dari notulen direksi sebagai keputusan resmi)

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~46% | Ada konflik: 340 (keuangan) vs 312 (HRD/direksi) vs 318 (audit) |
| Halusinasi | NO_CLAIMS / VERIFIED | Jawaban singkat, faktual |
| Konflik | 4-5 konflik | VALUE_CONFLICT antar dokumen |

**Poin demo:** Sistem memilih angka dari notulen direksi karena paling otoritatif (keputusan resmi), bukan dari laporan keuangan yang lebih dulu dibuat.

---

### 2. Berapa laba bersih perusahaan tahun 2024?

**Jawaban yang diharapkan:** Rp 10,5 miliar (dari notulen direksi, setelah koreksi pajak)

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | 0% | 3 angka berbeda: Rp 12M, Rp 10,5M, Rp 9,8M |
| Halusinasi | FLAGGED | Klaim ada di dokumen tapi dikontradiksi dokumen lain |
| Konflik | 5 konflik | VALUE_CONFLICT berat |

**Poin demo:** Confidence 0% bukan berarti salah — sistem jujur bahwa data sangat bertentangan. Auditor menyebut Rp 9,8M, direksi Rp 10,5M, laporan awal Rp 12M.

---

### 3. Versi berapa DataSync Pro yang terkini dan kapan diluncurkan?

**Jawaban yang diharapkan:** Versi 4.3, diluncurkan 10 November 2024

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~17% | Konflik dengan laporan keuangan yang menyebut v4.2 |
| Halusinasi | VERIFIED ✅ | Fakta terdukung kuat di laporan produk + notulen |
| Konflik | 5 konflik | TEMPORAL (tanggal berbeda antar dokumen) |

**Poin demo:** Meski confidence rendah karena konflik umum, status VERIFIED menunjukkan klaim spesifik ini terdukung dokumen.

---

### 4. Berapa pengguna aktif DataSync Pro?

**Jawaban yang diharapkan:** 9.800 perusahaan (berbayar aktif)

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~42% | Konflik: 12.500 (keuangan/sales) vs 9.800 (produk/direksi) |
| Halusinasi | VERIFIED ✅ | |
| Konflik | 0-1 konflik | Tergantung chunk yang di-retrieve |

**Poin demo:** Sistem menjelaskan perbedaan: 12.500 termasuk trial, 9.800 adalah berbayar. Ini contoh query yang jawabannya tepat tapi angkanya ambigu.

---

### 5. Di kota mana saja PT Teknologi Maju Indonesia memiliki kantor?

**Jawaban yang diharapkan:** Jakarta dan Surabaya (aktif); Bandung tutup Maret 2024; Medan rencana Q3 2025

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~7% | Laporan keuangan sebut 3 kantor (salah) |
| Halusinasi | VERIFIED ✅ | |
| Konflik | 5 konflik | TEMPORAL + VALUE conflict |

**Poin demo:** Laporan keuangan ketinggalan informasi penutupan kantor Bandung. Notulen dan HRD lebih akurat.

---

### 6. Kapan rencana peluncuran DataSync Pro versi 5.0?

**Jawaban yang diharapkan:** Q2 2025 (Juni), dengan kemungkinan mundur ke Q3 2025 (September)

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~8% | Tanggal berbeda di tiap dokumen |
| Halusinasi | FLAGGED | Klaim "Q2" ada tapi ada dokumen yang menyebut buffer Q3 |
| Konflik | 5 konflik | TEMPORAL_CONFLICT |

**Poin demo:** Contoh pertanyaan dengan jawaban yang memang tidak pasti karena dokumen sendiri memberikan range waktu.

---

### 7. Berapa target rekrutmen karyawan baru tahun 2025?

**Jawaban yang diharapkan:** 60 orang (keputusan resmi direksi), bukan 80 seperti di laporan keuangan

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | ~6% | Konflik: 80 (keuangan) vs 60 (HRD/direksi) |
| Halusinasi | VERIFIED ✅ | |
| Konflik | 4 konflik | VALUE_CONFLICT |

**Poin demo:** Laporan keuangan dibuat lebih awal sebelum keputusan final direksi. Sistem memilih data yang lebih baru dan otoritatif.

---

### 8. Apa hasil temuan audit eksternal terkait laba bersih perusahaan?

**Jawaban yang diharapkan:** Rp 9,8 miliar setelah koreksi PSAK 72

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | 0% | Konflik berat dengan semua laporan internal |
| Halusinasi | FLAGGED | Klaim ada di dokumen audit tapi dikontradiksi dokumen lain |
| Konflik | 4 konflik | VALUE_CONFLICT |

**Poin demo:** Pertanyaan spesifik ke sumber tertentu (audit). Jawaban benar dari konteks pertanyaan, tapi confidence tetap 0% karena konflik sistemik.

---

### 9. Berapa total aset perusahaan?

**Jawaban yang diharapkan:** Rp 90 miliar (setelah revaluasi auditor); laporan internal menyebut Rp 95 miliar

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | 0% | Rp 95M (keuangan) vs Rp 90M (audit) |
| Halusinasi | FLAGGED | |
| Konflik | 4 konflik | VALUE_CONFLICT |

**Poin demo:** Perbedaan karena revaluasi gedung Jakarta: laporan keuangan Rp 40M, auditor nilai wajar Rp 35M.

---

### 10. Siapa CEO dan jajaran direksi PT Teknologi Maju Indonesia?

**Jawaban yang diharapkan:** CEO Andi Wijaya, CFO Sri Mulyani, CTO Budi Hartono, COO Dewi Santoso, VP Sales Reza Akbar

| Output | Nilai | Penjelasan |
|--------|-------|------------|
| Confidence | 0% | Konflik umum antar dokumen menyebabkan penalty besar |
| Halusinasi | FLAGGED | Jawaban panjang (list), beberapa klaim neutral di NLI |
| Konflik | 5 konflik | |

**Poin demo:** Jawaban faktual benar, tapi confidence 0% karena penalty konflik dari VALUE_CONFLICT di dokumen lain. Ini menunjukkan bahwa confidence rendah bukan selalu berarti jawaban salah.

---

## Ringkasan Pola Output untuk Demo

| Pola | Contoh Pertanyaan | Pesan Demo |
|------|-------------------|------------|
| **VERIFIED + Confidence tinggi** | Pengguna aktif DataSync Pro | Data konsisten, tidak ada konflik pada pertanyaan spesifik ini |
| **VERIFIED + Confidence rendah** | Versi DataSync Pro terkini | Fakta benar tapi lingkungan dokumen penuh konflik |
| **FLAGGED + Konflik banyak** | Laba bersih 2024 | Data sangat bertentangan, perlu verifikasi manual |
| **NO_CLAIMS** | Pertanyaan dengan refusal | AI jujur tidak ada info cukup, tidak mengarang |
| **Confidence 0%** | Hampir semua | Bukan berarti salah — bisa karena banyak konflik |

---

## Tips Presentasi

1. **Mulai dengan pertanyaan 4** (pengguna aktif) — confidence relatif tinggi, jawaban bersih, tidak ada konflik. Tunjukkan sistem bekerja normal dulu.
2. **Lanjut pertanyaan 2** (laba bersih) — langsung terlihat 3 angka berbeda dan sistem mendeteksi konflik berat.
3. **Pertanyaan 10** (direksi) — tunjukkan bahwa FLAGGED tidak selalu berarti salah; jawabannya benar, tapi NLI tidak yakin karena kalimat panjang.
4. **Buka tab Konflik** — tunjukkan deskripsi TEMPORAL_CONFLICT dan VALUE_CONFLICT secara visual di UI.
5. **Buka tab Verifikasi Klaim** — tunjukkan score entailment per kalimat jawaban.
