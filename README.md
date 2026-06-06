# Nade AI — RAG System

Sistem tanya-jawab dokumen lokal berbasis Retrieval-Augmented Generation dengan deteksi konflik, halusinasi, dan pengenalan teks multibahasa.

**Preview UI:** http://deadyiss.github.io/nadeai/

---

## Fitur Utama

- Upload dokumen PDF, DOCX, TXT, dan foto/gambar
- OCR multibahasa (Indonesia & Inggris) untuk dokumen scan/foto
- Tanya-jawab berdasarkan isi dokumen (bukan pengetahuan umum AI)
- Deteksi konflik antar dokumen secara otomatis
- Verifikasi halusinasi jawaban AI menggunakan NLI model
- Document chunking — dokumen besar dibaca seluruhnya
- Multi-user dengan role Admin & User
- Antarmuka Web App modern + CLI
- Support LLM: Groq API (cloud) atau Ollama (lokal)

---

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.12, Flask + Waitress |
| LLM | Groq API atau Ollama (lokal) |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` |
| NLI (Hallucination) | `mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| Vector Search | In-memory NumPy + SQLite |
| OCR | RapidOCR + pytesseract + OpenCV |
| Database | SQLite via SQLAlchemy 2.0 |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |

---

## Deploy di Linux (Ubuntu 22.04 / 24.04 / 26.04)

### 1. Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  git \
  tesseract-ocr \
  tesseract-ocr-ind \
  tesseract-ocr-eng \
  libgl1 \
  libglib2.0-0t64 \
  libsm6 \
  libxrender1 \
  libxext6
```

### 2. Clone Repository

```bash
git clone <repo-url>
cd nadeai
```

### 3. Setup Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Konfigurasi `.env`

```bash
cp .env.example .env
nano .env
```

Pilih salah satu LLM provider:

**Opsi A — Groq API (recommended, lebih cepat):**
```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```
Dapatkan API key gratis di: https://console.groq.com

**Opsi B — Ollama (lokal, offline):**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_HOST=http://127.0.0.1:11434
```

### 6. Install Ollama (jika pakai Opsi B)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

Jalankan Ollama service (terminal terpisah):
```bash
ollama serve
```

### 7. Buat Folder & Init Database

```bash
mkdir -p data/{documents,uploads} logs
python3 -c "from models.database import init_db; init_db()"
```

Output yang diharapkan:
```
Database initialized successfully.
```

### 8. Jalankan Aplikasi

```bash
# Development
python3 app.py

# Production (LAN multi-user)
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### 9. Akses

```
http://localhost:5000
```

Login default: `admin` / `admin123`

Akses dari perangkat lain di LAN:
```bash
hostname -I   # cari IP laptop
# lalu buka: http://<IP>:5000
```

---

## Deploy di Windows

### 1. Install Python 3.12

Download dari: https://www.python.org/downloads/release/python-3120/

Pilih **Windows installer (64-bit)**, centang **Add Python to PATH** saat install.

Verifikasi:
```powershell
python --version
# Python 3.12.x
```

### 2. Install Tesseract OCR

Download installer dari: https://github.com/UB-Mannheim/tesseract/wiki

Pilih versi terbaru (64-bit). Saat install:
- Centang **Indonesian** dan **English** language data
- Catat lokasi install (default: `C:\Program Files\Tesseract-OCR\`)

Tambahkan ke PATH (jika belum otomatis):
```
System Properties → Environment Variables → Path → Add:
C:\Program Files\Tesseract-OCR\
```

Verifikasi:
```powershell
tesseract --version
```

### 3. Install Ollama (jika pakai LLM lokal)

Download dari: https://ollama.com/download/windows

Jalankan installer `.exe`, ikuti wizard.

Verifikasi:
```powershell
ollama --version
```

Pull model:
```powershell
ollama pull llama3.1:8b
```

### 4. Clone Repository

```powershell
git clone <repo-url>
cd nadeai
```

### 5. Setup Virtual Environment

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Jika muncul error ExecutionPolicy:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

Verifikasi Python di venv:
```powershell
python --version
# Python 3.12.x
```

### 6. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

Jika timeout saat download:
```powershell
pip install -r requirements.txt --timeout 120
```

### 7. Konfigurasi `.env`

```powershell
copy .env.example .env
notepad .env
```

Pilih salah satu LLM provider:

**Opsi A — Groq API (recommended):**
```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```
Dapatkan API key gratis di: https://console.groq.com

**Opsi B — Ollama (lokal, offline):**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
OLLAMA_HOST=http://127.0.0.1:11434
```

### 8. Buat Folder & Init Database

```powershell
mkdir data\documents, data\uploads, logs
python -c "from models.database import init_db; init_db()"
```

Output yang diharapkan:
```
Database initialized successfully.
```

### 9. Jalankan Ollama Service (jika pakai Opsi B)

Buka terminal baru (tanpa venv), jalankan:
```powershell
ollama serve
```

Biarkan terminal ini tetap terbuka selama aplikasi digunakan.

### 10. Jalankan Aplikasi

Kembali ke terminal venv:
```powershell
python app.py
```

### 11. Akses

```
http://localhost:5000
```

Login default: `admin` / `admin123`

Akses dari perangkat lain di LAN:
```powershell
ipconfig   # cari IPv4 Address
# lalu buka: http://<IP>:5000
```

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

Commands yang tersedia:
```
python cli.py interactive          # Mode interaktif
python cli.py upload <file>        # Upload dokumen
python cli.py query "<pertanyaan>" # Query langsung
python cli.py query "<teks>" --output json
python cli.py stats                # Statistik sistem
python cli.py users                # Daftar user
python cli.py documents            # Daftar dokumen
```

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

## Troubleshooting

### `No module named 'sqlalchemy'` atau module lain
```bash
# Linux
source venv/bin/activate
pip install -r requirements.txt

# Windows
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### `Failed to connect to Ollama`
Pastikan Ollama service berjalan:
```bash
ollama serve   # Linux
# atau buka Ollama dari Start Menu (Windows)
```

### `GROQ_API_KEY not set` atau `401 Unauthorized`
Pastikan `.env` berisi `GROQ_API_KEY=gsk_...` yang valid.

### Port 5000 sudah dipakai
```bash
# Linux
kill $(lsof -ti:5000)

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Database rusak / perlu reset
```bash
# Linux
rm data/app.db
python3 -c "from models.database import init_db; init_db()"

# Windows
del data\app.db
python -c "from models.database import init_db; init_db()"
```

> **Hati-hati:** semua data (dokumen, user, history) akan hilang.

### Tesseract tidak ditemukan (Windows)
Tambahkan path ke `config.py` setelah baris `import config`:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

## Estimasi Waktu per Query

| Tahap | Waktu |
|-------|-------|
| Embedding query | ~5ms |
| Similarity search | ~100-500ms |
| Conflict detection | <1ms |
| LLM via Groq API | ~400-800ms |
| LLM via Ollama (CPU) | ~10-60s |
| Hallucination check (NLI, CPU) | ~6-15 detik |
| **Total (Groq)** | **~7-16 detik** |
| **Total (Ollama CPU)** | **~20-80 detik** |

---

## Dokumentasi

- [Prerequisites](docs/getting-started/prerequisites.md)
- [Instalasi](docs/getting-started/installation.md)
- [Cara Menjalankan](docs/getting-started/CARA-START.md)
- [Konsep Sistem](docs/concept.md)
- [Arsitektur](docs/architecture/system-overview.md)
- [Alur Data](docs/architecture/data-flow.md)
- [Tech Stack](docs/architecture/tech-stack.md)
- [Algoritma](docs/algorithms/algorithms.md)
- [Struktur Project](docs/development/project-structure.md)
- [Worklog](docs/Worklog.md)