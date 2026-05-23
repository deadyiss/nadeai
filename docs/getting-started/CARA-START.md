# Cara Menjalankan Aplikasi

## Persiapan (Satu Kali)

Pastikan sudah menyelesaikan instalasi. Setiap kali membuka terminal baru, aktifkan virtual environment terlebih dahulu:

```bash
cd /home/deadyiss/Downloads/tugas-ai
source venv/bin/activate
```

---

## Menjalankan Web App

```bash
python3 app.py
```

Tunggu hingga muncul output:
```
Bootstrap complete.
Starting server: http://0.0.0.0:5000 (env=development)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

> **Catatan:** Boot pertama lebih lama (~15-20 detik) karena sistem mendownload dan memuat model embedding (~471MB) dan NLI (~560MB). Boot berikutnya ~5 detik karena model sudah di-cache.

Buka browser:
```
http://localhost:5000
```

Login dengan:
- Username: `admin`
- Password: `admin123`

---

## Menjalankan CLI

Untuk mode command-line tanpa server web:

```bash
# Mode interaktif (chat)
python3 cli.py interactive

# Query langsung
python3 cli.py query "berapa anggaran proyek?"

# Upload dokumen via CLI
python3 cli.py upload /path/ke/dokumen.pdf

# Lihat statistik
python3 cli.py stats

# Lihat daftar dokumen
python3 cli.py documents

# Lihat daftar user
python3 cli.py users
```

---

## Akses dari Perangkat Lain (LAN)

Aplikasi berjalan di `0.0.0.0:5000` sehingga bisa diakses dari perangkat lain di jaringan yang sama.

1. Cari IP laptop server:
```bash
hostname -I
# contoh output: 192.168.1.15
```

2. Buka dari HP/tablet/laptop lain:
```
http://192.168.1.15:5000
```

---

## Health Check

Cek status sistem (DB, LLM, Vector Store):

```bash
curl http://localhost:5000/health
```

Respon normal:
```json
{
  "data": {
    "checks": {
      "database": "ok",
      "llm": "ok",
      "vector_store": "ok (15 vectors)"
    },
    "status": "healthy"
  }
}
```

---

## Memahami Output di Web

Setelah mengajukan pertanyaan, sistem menampilkan beberapa indikator. Berikut penjelasan lengkapnya:

---

### Confidence (%)

Angka 0–100% yang menunjukkan seberapa yakin sistem terhadap jawaban.

| Nilai | Arti |
|-------|------|
| ≥ 70% | **Tinggi** — jawaban kuat, dokumen relevan jelas, tidak ada konflik besar |
| 40–69% | **Sedang** — ada sedikit ketidakpastian, perlu dicermati |
| < 40% | **Rendah** — banyak konflik atau klaim tidak terverifikasi, cek manual |
| 0% | **Sangat rendah** — konflik berat + hampir semua klaim tidak terdukung dokumen |

**Formula:**
```
base = rata-rata similarity chunk yang ditemukan
score = base × (1 - hallucination_score)
jika ada konflik: score - 0.2
```

> Confidence 0% bukan berarti jawaban salah — bisa berarti dokumen memang saling bertentangan (konflik) sehingga sistem tidak berani memberikan angka tinggi.

---

### Hallucination (Status Verifikasi Klaim)

Sistem memeriksa setiap kalimat dalam jawaban AI — apakah kalimat itu benar-benar ada dukungannya di dokumen, atau AI mengarang.

| Status | Arti |
|--------|------|
| **VERIFIED** ✅ | Semua klaim dalam jawaban terbukti ada di dokumen sumber |
| **FLAGGED** ⚠️ | Satu atau lebih klaim tidak terdukung / bertentangan dengan dokumen |
| **NO_CLAIMS** ℹ️ | Jawaban berupa penolakan ("tidak ada informasi") atau terlalu pendek untuk diverifikasi — ini aman, bukan error |

**Detail per klaim** (tab "Verifikasi Klaim"):
- `entail: 0.94` → probabilitas klaim didukung dokumen (semakin tinggi semakin baik)
- `contradict: 0.02` → probabilitas klaim bertentangan dokumen (semakin rendah semakin baik)
- `verdict: entailment` → keputusan akhir: entailment / neutral / contradiction / no_context
- `source: nama_file.pdf` → chunk dokumen mana yang jadi acuan verifikasi

> **Catatan penting:** FLAGGED tidak selalu berarti AI berbohong. Bisa juga berarti klaim terlalu umum / wording berbeda dari dokumen, sehingga NLI tidak yakin. Baca klaim dan verdict-nya untuk menilai sendiri.

---

### Conflict (Konflik Antar Dokumen)

Sistem secara otomatis mendeteksi jika dokumen-dokumen yang di-upload saling bertentangan.

| Status | Arti |
|--------|------|
| **NONE** ✅ | Tidak ditemukan pertentangan antar dokumen |
| **DETECTED** ⚠️ | Ada satu atau lebih konflik antar dokumen |

**Angka di sebelahnya** (misal "5 ditemukan") = jumlah total konflik yang terdeteksi dari semua jenis.

**Tiga jenis konflik** (tab "Konflik"):

| Tipe | Severity | Arti | Contoh |
|------|----------|------|--------|
| `TEMPORAL_CONFLICT` | 🔴 HIGH | Dokumen menyebut tanggal berbeda untuk hal yang sama | Dok A: "mulai 1 Jan 2025", Dok B: "mulai 15 Jan 2025" |
| `VALUE_CONFLICT` | 🔴 HIGH | Dokumen menyebut nilai angka berbeda | Dok A: "Rp 50 juta", Dok B: "Rp 75 juta", Dok C: "Rp 85 juta" |
| `MULTI_SOURCE` | 🟡 MEDIUM | Topik yang sama muncul di ≥3 dokumen dengan relevansi tinggi | Potensi inkonsistensi, belum tentu langsung bertentangan |

**Apa yang harus dilakukan jika ada konflik?**
- Buka tab "Konflik" untuk lihat deskripsi lengkap dan dokumen mana yang bertentangan
- Cek dokumen sumber aslinya untuk verifikasi mana yang benar
- Konflik HIGH perlu perhatian serius; konflik MEDIUM bisa jadi hanya perspektif berbeda

---

### Tab Sumber

Menampilkan daftar chunk dokumen yang dipakai sistem untuk menjawab pertanyaan.

- `#ID` → nomor chunk di database
- `nama_file.pdf` → nama dokumen asli
- `sim 0.647` → similarity score: seberapa mirip chunk ini dengan pertanyaan (0–1, semakin tinggi semakin relevan)

> Jika similarity semua sumber rendah (< 0.3), kemungkinan besar dokumen yang di-upload tidak mengandung jawaban atas pertanyaan tersebut.

---

### Tab Timing

Menampilkan waktu yang dipakai setiap tahap pipeline:

| Kolom | Arti |
|-------|------|
| Search | Waktu cari chunk relevan di vector store |
| Conflict | Waktu deteksi konflik antar dokumen |
| LLM | Waktu Groq API generate jawaban |
| Hallucination | Waktu NLI verifikasi klaim (biasanya paling lama) |
| Total | Total waktu keseluruhan |

---

### Contoh Interpretasi Hasil Nyata

```
Pertanyaan : "Berapa total anggaran proyek SmartCity Bandung?"
Jawaban    : "Total anggaran proyek SmartCity Bandung adalah Rp 85 juta [Document 3]."

Confidence    : 0%
Hallucination : FLAGGED
Conflict      : DETECTED (5 konflik)
```

**Interpretasi:**
- Jawaban **Rp 85 juta** diambil dari Notulen Rapat Direksi — secara logika ini paling otoritatif (keputusan resmi).
- **Confidence 0%** karena ditemukan 5 konflik (anggaran berbeda di 4 dokumen: 50, 72, 75, 85 juta), sehingga penalty konflik besar.
- **FLAGGED** karena klaim "Rp 85 juta" memang ada di dokumen, tapi dokumen lain menyebut angka berbeda — NLI mendeteksi ambiguitas ini.
- **Kesimpulan untuk user:** Jawaban bisa benar, tapi harus cek tab Konflik dan verifikasi sendiri ke dokumen asli mana yang paling valid.

---

## Estimasi Waktu per Query

| Tahap | Waktu |
|-------|-------|
| Embedding query | ~5ms |
| Similarity search | ~100-500ms |
| Conflict detection | <1ms |
| LLM via Groq API | ~400-800ms |
| Hallucination check (NLI, CPU) | ~6-15 detik |
| **Total** | **~7-16 detik** |

> NLI berjalan di CPU. Waktu bervariasi tergantung panjang jawaban LLM (lebih panjang = lebih banyak klaim = lebih lama).

---

## Troubleshooting

### Error: `GROQ_API_KEY not set` atau `401 Unauthorized`
Pastikan file `.env` berisi `GROQ_API_KEY=gsk_...` yang valid.

### Error: `No module named 'groq'`
```bash
source venv/bin/activate
pip install groq
```

### Error saat boot: model download gagal
Pastikan ada koneksi internet saat pertama kali menjalankan. Model akan diunduh dari HuggingFace.

### Port 5000 sudah dipakai
```bash
kill $(lsof -ti:5000)
python3 app.py
```

### Database rusak / perlu reset
```bash
rm data/app.db
python3 -c "from models.database import init_db; init_db()"
```
> **Hati-hati:** semua data (dokumen, user, history) akan hilang.
