# Project Structure

```
tugas-ai/
├── app.py                    # Entry point web app (Flask + Waitress)
├── cli.py                    # Entry point CLI
├── config.py                 # Konfigurasi dari .env
├── requirements.txt          # Python dependencies
├── .env                      # Variabel environment (tidak di-commit)
│
├── core/                     # Business logic utama
│   ├── __init__.py
│   ├── document_processor.py # Extract teks dari PDF/DOCX/TXT/gambar
│   ├── ocr_engine.py         # RapidOCR + pytesseract
│   ├── embedding_engine.py   # Teks → vector 384-dim (singleton)
│   ├── vector_store.py       # In-memory search + SQLite persistence
│   ├── conflict_detector.py  # Deteksi TEMPORAL/VALUE/MULTI_SOURCE
│   ├── hallucination_checker.py  # NLI two-stage verification (singleton)
│   ├── llm_engine.py         # Groq API client + prompt builder
│   ├── query_processor.py    # Orchestrator pipeline RAG lengkap
│   └── auth_manager.py       # Register/login/logout/verify token
│
├── models/                   # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── database.py           # Engine, SessionLocal, init_db()
│   ├── user.py
│   ├── document.py           # Termasuk chunk_index, chunk_total
│   ├── embedding.py
│   ├── query_history.py
│   ├── session.py
│   └── conflict_log.py
│
├── routes/                   # Flask Blueprints (HTTP endpoints)
│   ├── __init__.py           # Decorator require_auth, require_admin
│   ├── auth_routes.py        # POST /auth/login, /register, /logout; GET /auth/me
│   ├── document_routes.py    # POST /api/upload; GET /api/documents; DELETE /api/document/<id>
│   ├── query_routes.py       # POST /api/query
│   ├── admin_routes.py       # GET /admin/dashboard, /users, /documents, /queries
│   └── health_routes.py      # GET /health
│
├── utils/                    # Helper functions
│   ├── __init__.py
│   ├── date_extractor.py     # Regex ekstrak tanggal (ISO + Indo format)
│   ├── text_cleaner.py       # clean_text(), chunk_text(), count_words()
│   ├── file_validator.py     # Validasi ekstensi + ukuran file
│   ├── response_builder.py   # success_response(), error_response()
│   └── logger.py             # Rotating file logger + console
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html            # Halaman utama (query + upload)
│   ├── login.html
│   ├── register.html
│   └── admin/
│       ├── dashboard.html
│       ├── users.html
│       └── documents.html
│
├── static/                   # Assets statis
│   ├── css/style.css         # Satu file CSS (termasuk modal + pagination)
│   └── js/
│       ├── main.js           # Logic query, upload, pagination dokumen
│       ├── auth.js           # Auth, Toast, Modal utilities
│       └── admin.js          # Logic halaman admin
│
├── data/                     # ⚠️ Tidak di-commit
│   ├── documents/
│   │   └── <user_id>/        # File dokumen per user
│   ├── uploads/              # Temp upload sebelum diproses
│   └── app.db                # SQLite database
│
├── logs/                     # ⚠️ Tidak di-commit
│   └── app.log
│
└── docs/
    ├── Worklog.md            # Catatan pengerjaan lengkap (jangan diubah)
    ├── concept.md
    ├── getting-started/
    │   ├── prerequisites.md
    │   ├── installation.md
    │   └── CARA-START.md     # Cara menjalankan aplikasi
    ├── architecture/
    │   ├── system-overview.md
    │   ├── data-flow.md
    │   └── tech-stack.md
    ├── algorithms/
    │   └── algorithms.md
    └── development/
        └── project-structure.md  (file ini)
```

---

## Environment Variables (.env)

```env
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=<random-string-panjang>

DATABASE_URL=sqlite:///data/app.db
MAX_FILE_SIZE_MB=100

LLM_PROVIDER=groq
LLM_MODEL=llama-3.1-8b-instant
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXX

EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

HALLUCINATION_THRESHOLD=0.6
TOP_K_DOCUMENTS=5
SIMILARITY_MIN_THRESHOLD=0.15

NLI_ENTAILMENT_THRESHOLD=0.5
NLI_CONTRADICTION_THRESHOLD=0.5

SESSION_EXPIRE_HOURS=24
LOG_LEVEL=INFO

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@local
```

---

## .gitignore

```
venv/
__pycache__/
*.pyc
.env
data/app.db
data/documents/
data/uploads/
logs/
.DS_Store
.vscode/settings.json
.cache/
```

---

## Format File yang Didukung

| Format | Engine | Catatan |
|--------|--------|---------|
| `.pdf` | pypdf | Auto-fallback OCR jika teks < 50 char |
| `.docx` | python-docx | Termasuk tabel |
| `.txt` | open() UTF-8 | Plain text |
| `.jpg`, `.jpeg` | RapidOCR + tesseract | OCR |
| `.png` | RapidOCR + tesseract | OCR |
| `.bmp`, `.tiff` | RapidOCR + tesseract | OCR |
