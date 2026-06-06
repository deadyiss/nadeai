# Cara Menjalankan

## Linux

```bash
cd /path/ke/nadeai
source venv/bin/activate
python3 app.py
```

## Windows

```powershell
cd C:\path\ke\nadeai
.\venv\Scripts\Activate.ps1
python app.py
```

Tunggu output:
```
Database initialized successfully.
Bootstrap selesai.
Server berjalan: http://0.0.0.0:5000 (env=development)
```

Boot pertama ~15-20 detik (download + load model). Boot berikutnya ~5 detik.

Buka: `http://localhost:5000` — login `admin` / `admin123`

---

## Akses dari Perangkat Lain (LAN)

```bash
# Linux — cari IP
hostname -I

# Windows — cari IP
ipconfig   # lihat IPv4 Address
```

Buka dari HP/laptop lain di jaringan yang sama: `http://<IP>:5000`

---

## CLI

```bash
# Linux
source venv/bin/activate
python3 cli.py interactive

# Windows
.\venv\Scripts\Activate.ps1
python cli.py interactive
```

Commands:
```
python3 cli.py interactive          # Mode chat interaktif
python3 cli.py upload <file>        # Upload dokumen
python3 cli.py query "<pertanyaan>" # Query langsung
python3 cli.py query "<teks>" --output json
python3 cli.py stats                # Statistik sistem
python3 cli.py users                # Daftar user
python3 cli.py documents            # Daftar dokumen
```

---

## Menggunakan Ollama (LLM Lokal, Opsional)

Jalankan Ollama di terminal terpisah **sebelum** `app.py`:
```bash
ollama serve
```

Lalu di `.env` ganti:
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_HOST=http://127.0.0.1:11434
```

> Ollama di CPU sangat lambat (~25-90 detik/query). Groq API direkomendasikan.

---

## Health Check

```bash
curl http://localhost:5000/health
```

Response normal:
```json
{
  "data": {
    "checks": {
      "database": "ok",
      "llm": "ok",
      "vector_store": "ok (0 vectors)"
    },
    "status": "healthy"
  }
}
```

---

## Memahami Output Query

**Confidence (%):** Seberapa yakin sistem terhadap jawaban. Formula:
```
base = avg(similarity chunks yang di-retrieve)
score = base × (1 - hallucination_score)
jika ada konflik: score - 0.2
clamp(0, 1)
```
Confidence 0% tidak berarti jawaban salah — bisa berarti dokumen saling bertentangan.

**Hallucination Status:**
- `VERIFIED` — semua klaim terdukung dokumen
- `FLAGGED` — satu atau lebih klaim tidak terdukung/bertentangan
- `NO_CLAIMS` — jawaban berupa refusal ("tidak ada informasi") — ini aman

**Conflict:**
- `TEMPORAL_CONFLICT` (HIGH) — dokumen berbeda menyebut tanggal berbeda
- `VALUE_CONFLICT` (HIGH) — dokumen berbeda menyebut angka berbeda (>10% selisih)
- `MULTI_SOURCE` (MEDIUM) — topik muncul di ≥3 dokumen dengan similarity tinggi

---

## Troubleshooting Cepat

| Error | Solusi |
|-------|--------|
| `No module named 'xxx'` | `source venv/bin/activate` lalu `pip install -r requirements.txt` |
| `GROQ_API_KEY not set` | Isi `.env` dengan `GROQ_API_KEY=gsk_...` |
| `401 Unauthorized` (Groq) | API key tidak valid atau expired — buat key baru di console.groq.com |
| `Failed to connect to Ollama` | Jalankan `ollama serve` di terminal terpisah |
| Port 5000 sudah dipakai | `kill $(lsof -ti:5000)` (Linux) atau `taskkill /PID <PID> /F` (Windows) |
| Database rusak | `rm data/app.db` lalu `python3 -c "from models.database import init_db; init_db()"` |
| Tesseract not found (Windows) | Tambah `C:\Program Files\Tesseract-OCR\` ke PATH |

> Reset database menghapus semua data: user, dokumen, history.
