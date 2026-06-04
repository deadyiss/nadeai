# RAG System — Tanya Jawab Berbasis Dokumen

Sistem tanya-jawab cerdas berbasis dokumen menggunakan Retrieval-Augmented Generation (RAG), dilengkapi deteksi konflik antar dokumen dan verifikasi halusinasi AI secara otomatis.

## Preview 
Link : http://deadyiss.github.io/nadeai/


## Fitur Utama

- Upload dokumen PDF, DOCX, TXT, dan foto/gambar
- OCR multibahasa (Indonesia & Inggris) untuk dokumen scan/foto
- Tanya-jawab berdasarkan isi dokumen (bukan pengetahuan umum AI)
- Deteksi konflik antar dokumen secara otomatis
- Verifikasi halusinasi jawaban AI menggunakan NLI model
- Document chunking — dokumen besar dibaca seluruhnya
- Multi-user dengan role Admin & User
- Antarmuka Web App modern + CLI

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.14, Flask + Waitress |
| LLM | Groq API (`llama-3.1-8b-instant`) |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` |
| NLI (Hallucination) | `mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` |
| Vector Search | In-memory NumPy + SQLite |
| OCR | RapidOCR + pytesseract + OpenCV |
| Database | SQLite via SQLAlchemy 2.0 |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |

## Quick Start

```bash
# 1. Clone & masuk ke direktori
git clone <repo-url>
cd tugas-ai

# 2. Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Konfigurasi .env
cp .env.example .env
# Edit .env — isi GROQ_API_KEY (lihat docs/getting-started/prerequisites.md)

# 5. Inisialisasi database
python3 -c "from models.database import init_db; init_db()"

# 6. Jalankan aplikasi
python3 app.py
```

Akses di browser: `http://localhost:5000`
Login default: `admin` / `admin123`

## Dokumentasi

- [Prerequisites & Setup](docs/getting-started/prerequisites.md)
- [Cara Instalasi](docs/getting-started/installation.md)
- [Cara Menjalankan](docs/getting-started/CARA-START.md)
- [Konsep Sistem](docs/concept.md)
- [Arsitektur](docs/architecture/system-overview.md)
- [Alur Data](docs/architecture/data-flow.md)
- [Tech Stack Detail](docs/architecture/tech-stack.md)
- [Algoritma](docs/algorithms/algorithms.md)
- [Struktur Project](docs/development/project-structure.md)
- [Worklog](docs/Worklog.md)
