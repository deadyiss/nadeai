# Instalasi

## 1. Clone Repository

```bash
git clone <repo-url>
cd tugas-ai
```

---

## 2. Buat Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> Proses ini mengunduh semua library Python yang dibutuhkan (~300MB).

---

## 4. Konfigurasi `.env`

Buat file `.env` di root project:

```bash
cp .env.example .env   # jika tersedia
# atau buat manual:
nano .env
```

Isi file `.env`:

```env
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=ganti-dengan-string-acak-panjang

DATABASE_URL=sqlite:///data/app.db
MAX_FILE_SIZE_MB=100

LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXX

EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

HALLUCINATION_THRESHOLD=0.6
TOP_K_DOCUMENTS=5
SIMILARITY_MIN_THRESHOLD=0.15

SESSION_EXPIRE_HOURS=24
LOG_LEVEL=INFO

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@local
```

> **Penting:** Ganti `GROQ_API_KEY` dengan API key dari [console.groq.com](https://console.groq.com).
> Ganti `SECRET_KEY` dengan string acak panjang untuk keamanan sesi.

---

## 5. Buat Folder yang Diperlukan

```bash
mkdir -p data/{documents,uploads} logs
```

---

## 6. Inisialisasi Database

```bash
python3 -c "from models.database import init_db; init_db()"
```

Output yang diharapkan:
```
Database initialized. Tables: users, documents, embeddings_cache, query_history, sessions, conflicts_log
Admin user created: admin
```

---

## 7. Verifikasi Instalasi

```bash
python3 -c "
import config
print('LLM Provider:', config.LLM_PROVIDER)
print('LLM Model:', config.LLM_MODEL)
print('Groq Key:', config.GROQ_API_KEY[:10] + '...')
print('DB:', config.DATABASE_URL)
"
```

Jika muncul nilai yang benar, instalasi selesai. Lanjut ke **Cara Menjalankan**.
