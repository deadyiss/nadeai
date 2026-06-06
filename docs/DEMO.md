# Demo Guide — Nade AI

Panduan lengkap untuk melakukan demo sistem menggunakan 7 dokumen fiktif PT Teknologi Maju Indonesia yang sengaja berisi data bertentangan antar divisi.

---

## Persiapan

### 1. Jalankan Aplikasi

**Linux:**
```bash
cd /path/ke/nadeai
source venv/bin/activate
python3 app.py
```

**Windows:**
```powershell
cd C:\path\ke\nadeai
.\venv\Scripts\Activate.ps1
python app.py
```

Tunggu output:
```
Bootstrap selesai.
Server berjalan: http://0.0.0.0:5000
```

Buka browser: `http://localhost:5000` — login `admin` / `admin123`

---

### 2. Upload Dokumen Demo

Semua file demo ada di folder `demo_docs/`. Upload ketujuh file berikut via halaman utama — centang **Shared** agar semua user bisa mengakses.

| File | Isi | Tanggal |
|------|-----|---------|
| `laporan_keuangan_2024.docx` | Laporan tahunan divisi Keuangan | 31 Des 2024 |
| `laporan_hrd_2024.docx` | Laporan SDM divisi HR | 15 Jan 2025 |
| `laporan_produk_datasync.docx` | Status produk DataSync Pro | 20 Jan 2025 |
| `notulen_rapat_direksi_jan2025.docx` | Keputusan resmi direksi | 10 Jan 2025 |
| `audit_eksternal_2024.docx` | Temuan auditor independen | 25 Jan 2025 |
| `laporan_sales_q4_2024.docx` | Performa sales Q4 | Des 2024 |
| `rencana_teknologi_2025.docx` | Roadmap engineering | 8 Jan 2025 |

Upload satu per satu, tunggu notifikasi "berhasil diupload" setiap kali sebelum lanjut ke file berikutnya.

---

## Konflik yang Ditanam

Ini adalah konflik yang sengaja dibuat antar dokumen — inilah yang akan dideteksi sistem:

| Topik | Laporan Keuangan | HRD / Direksi | Audit |
|-------|-----------------|---------------|-------|
| Jumlah karyawan | 340 | 312 | 318 |
| Laba bersih 2024 | Rp 12M | Rp 10,5M | Rp 9,8M |
| Total aset | Rp 95M | — | Rp 90M |
| Versi DataSync Pro | 4.2 | 4.3 | — |
| Target rekrutmen | 80 orang | 60 orang | — |
| Kantor aktif | 3 (Bdg masih ada) | 2 (Bdg tutup Mar '24) | — |
| Pengguna berbayar | 12.500 (termasuk trial) | 9.800 (berbayar saja) | 8.900 |

---

## 10 Pertanyaan Demo

Urutan direkomendasikan dari yang paling bersih ke yang paling konfliktual.

---

### 1. Siapa CEO dan jajaran direksi perusahaan?

**Ketik:** `Siapa CEO dan jajaran direksi PT Teknologi Maju Indonesia?`

**Jawaban yang diharapkan:** CEO Andi Wijaya, CFO Sri Mulyani, CTO Budi Hartono, COO Dewi Santoso, VP Sales Reza Akbar.

**Yang menarik untuk ditunjukkan:** Jawaban faktual benar. Confidence mungkin rendah karena konflik sistemik di dokumen lain, bukan karena data direksi salah. Ini contoh bahwa **confidence rendah ≠ jawaban salah**.

---

### 2. Berapa harga paket DataSync Pro Enterprise?

**Ketik:** `Berapa harga langganan DataSync Pro paket Enterprise?`

**Jawaban yang diharapkan:** Rp 5 juta per bulan.

**Yang menarik untuk ditunjukkan:** Confidence relatif tinggi karena data ini konsisten di semua dokumen. Tunjukkan ini sebagai baseline "sistem berjalan normal".

---

### 3. Berapa pengguna aktif DataSync Pro?

**Ketik:** `Berapa jumlah pengguna aktif DataSync Pro saat ini?`

**Jawaban yang diharapkan:** Sistem menyebut 9.800 berbayar atau 12.500 total — tergantung chunk yang di-retrieve.

**Yang menarik untuk ditunjukkan:** Sistem idealnya menjelaskan perbedaan: 12.500 = berbayar + trial, 9.800 = berbayar aktif, 8.900 = berbayar ≥3 bulan berturut-turut. Buka tab **Konflik** untuk lihat VALUE_CONFLICT terdeteksi.

---

### 4. Versi berapa DataSync Pro yang terkini?

**Ketik:** `DataSync Pro versi berapa yang terbaru sekarang dan kapan dirilis?`

**Jawaban yang diharapkan:** Versi 4.3, rilis 10 November 2024.

**Yang menarik untuk ditunjukkan:** Confidence rendah karena laporan keuangan menyebut v4.2 (data lama). Buka tab **Konflik** — TEMPORAL_CONFLICT muncul karena dua tanggal berbeda (Agustus vs November 2024). Status hallucination: VERIFIED karena fakta v4.3 memang ada di dokumen.

---

### 5. Di kota mana saja perusahaan memiliki kantor?

**Ketik:** `Di kota mana saja PT Teknologi Maju Indonesia punya kantor aktif?`

**Jawaban yang diharapkan:** Jakarta dan Surabaya aktif; Bandung sudah tutup sejak Maret 2024; Medan rencana Q3 2025.

**Yang menarik untuk ditunjukkan:** Laporan keuangan (data lama) menyebut 3 kantor termasuk Bandung. HRD dan notulen direksi mengkonfirmasi Bandung sudah tutup. Sistem harus pilih data terbaru — tunjukkan TEMPORAL_CONFLICT di tab Konflik.

---

### 6. Berapa jumlah karyawan perusahaan?

**Ketik:** `Berapa total karyawan PT Teknologi Maju Indonesia?`

**Jawaban yang diharapkan:** 312 orang (keputusan resmi direksi), meski laporan lain menyebut 340 atau 318.

**Yang menarik untuk ditunjukkan:** Ini salah satu pertanyaan dengan konflik paling banyak. Buka tab **Konflik** — VALUE_CONFLICT HIGH dengan 3 angka berbeda. Confidence sangat rendah atau 0%. Tunjukkan ini ke audiens: sistem jujur mengakui data bertentangan.

---

### 7. Berapa laba bersih perusahaan tahun 2024?

**Ketik:** `Berapa laba bersih PT Teknologi Maju Indonesia tahun 2024?`

**Jawaban yang diharapkan:** Jawaban akan menyebut salah satu dari: Rp 12M (keuangan), Rp 10,5M (direksi), atau Rp 9,8M (audit).

**Yang menarik untuk ditunjukkan:** Confidence 0%. Tiga sumber berbeda, semua otoritatif. Buka tab **Konflik** — 5 konflik terdeteksi. Buka tab **Verifikasi Klaim** — lihat entailment dan contradiction score per kalimat jawaban. **Ini adalah showcase utama sistem.**

---

### 8. Kapan rencana rilis DataSync Pro v5.0?

**Ketik:** `Kapan DataSync Pro versi 5.0 akan dirilis?`

**Jawaban yang diharapkan:** Q2 2025 (target Juni), dengan kemungkinan mundur hingga Q3 2025 (September).

**Yang menarik untuk ditunjukkan:** TEMPORAL_CONFLICT — dua dokumen menyebut timeline berbeda (Juni vs September). Status FLAGGED karena ada range waktu. Ini contoh pertanyaan dengan jawaban yang memang tidak pasti secara dokumen.

---

### 9. Berapa target rekrutmen karyawan baru 2025?

**Ketik:** `Berapa target rekrutmen karyawan baru PT Teknologi Maju Indonesia di tahun 2025?`

**Jawaban yang diharapkan:** 60 orang (keputusan resmi direksi), bukan 80 seperti di laporan keuangan.

**Yang menarik untuk ditunjukkan:** VALUE_CONFLICT antara 80 (keuangan, data awal) vs 60 (direksi, keputusan final). Tunjukkan bahwa notulen rapat direksi adalah dokumen paling otoritatif — dan sistem mengambil jawaban dari sana.

---

### 10. Apa hasil temuan utama audit eksternal?

**Ketik:** `Apa temuan utama auditor eksternal tentang keuangan perusahaan tahun 2024?`

**Jawaban yang diharapkan:** Pendapatan aktual Rp 45,7M (selisih Rp 2,3M dari laporan), laba bersih Rp 9,8M, opini WDP atas PSAK 72.

**Yang menarik untuk ditunjukkan:** Pertanyaan yang diarahkan ke sumber spesifik. Jawaban benar, tapi confidence 0% karena konflik dengan semua laporan internal. Status FLAGGED. Ini contoh: pertanyaan tepat + sumber tepat + jawaban benar + confidence tetap rendah karena konteks dokumen keseluruhan penuh konflik.

---

## Alur Presentasi yang Disarankan

```
1. Upload semua dokumen (~3 menit)
   └─ Tunjukkan progress "14 chunks" dll di notifikasi

2. Pertanyaan 2 — harga Enterprise        (confidence tinggi, no conflict)
   └─ "Ini cara sistem bekerja normal"

3. Pertanyaan 7 — laba bersih             (showcase utama, 5 konflik)
   └─ Buka tab Konflik + Verifikasi Klaim
   └─ "Inilah mengapa kita butuh conflict detection"

4. Pertanyaan 4 — versi DataSync Pro      (VERIFIED + confidence rendah)
   └─ "Verified bukan berarti tidak ada masalah di dokumen lain"

5. Pertanyaan 6 — jumlah karyawan         (3 angka berbeda)
   └─ "Confidence 0% bukan berarti jawaban salah"

6. Pertanyaan 10 — temuan audit           (directed source question)
   └─ "Pertanyaan spesifik ke sumber yang tepat"

7. Pertanyaan 1 — direksi                 (factual correct, low confidence)
   └─ "Takeaway: selalu baca tab Konflik dan Verifikasi Klaim"
```

---

## Cara Membaca Output

| Indikator | Nilai | Interpretasi |
|-----------|-------|-------------|
| Confidence | ≥ 70% | Jawaban kuat, dokumen konsisten |
| Confidence | 0% | Konflik berat — cek tab Konflik |
| Hallucination | VERIFIED | Klaim terbukti ada di dokumen |
| Hallucination | FLAGGED | Klaim tidak terdukung atau dikontradiksi |
| Hallucination | NO_CLAIMS | AI refusal (tidak mengarang) — ini aman |
| Konflik | HIGH | Perlu verifikasi manual ke dokumen asli |
| Konflik | MEDIUM | Potensi inkonsistensi, tidak selalu salah |

**Pesan kunci untuk audiens:** Confidence 0% bukan kegagalan sistem — itu kejujuran sistem bahwa data sumber memang bertentangan. Ini lebih baik dari AI yang memberikan jawaban palsu dengan confidence tinggi.
