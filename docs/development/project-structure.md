# Project Structure

```
nadeai/
├── app.py                        # Entry point web app (Flask + Waitress)
├── cli.py                        # Entry point CLI (bypass auth, pakai admin)
├── config.py                     # Konfigurasi dari .env
├── requirements.txt              # Python dependencies (production)
├── requirements-dev.txt          # Dependencies testing & linting
├── pytest.ini                    # Konfigurasi pytest
├── render.yaml                   # Render.com deploy config (opsional)
├── .env                          # Secrets — tidak di-commit
├── .env.example                  # Template .env
├── .gitignore
│
├── core/                         # Business logic utama
│   ├── __init__.py
│   ├── auth_manager.py           # Register/login/logout/verify token/ensure_admin
│   ├── conflict_detector.py      # TEMPORAL / VALUE / MULTI_SOURCE detection
│   ├── document_processor.py     # Extract teks dari PDF/DOCX/TXT/gambar
│   ├── embedding_engine.py       # Singleton: teks → 384-dim vector
│   ├── hallucination_checker.py  # Singleton: cosine gate + NLI two-stage
│   ├── llm_engine.py             # Groq API + Ollama dual-provider
│   ├── ocr_engine.py             # RapidOCR + pytesseract + OpenCV
│   ├── query_processor.py        # Orchestrator pipeline RAG lengkap
│   └── vector_store.py           # Singleton: in-memory NumPy + SQLite cache
│
├── models/                       # SQLAlchemy ORM
│   ├── __init__.py               # Export semua model (penting untuk SA registry)
│   ├── conflict_log.py
│   ├── database.py               # Engine, SessionLocal, get_session(), init_db()
│   ├── document.py               # + chunk_index, chunk_total
│   ├── embedding.py              # EmbeddingCache alias
│   ├── query_history.py
│   ├── session.py
│   └── user.py
│
├── routes/                       # Flask Blueprints (JSON API)
│   ├── __init__.py               # Decorator require_auth, require_admin
│   ├── admin_routes.py           # /api/admin/* (dashboard, users, documents, queries)
│   ├── auth_routes.py            # /auth/login, /register, /logout, /me
│   ├── document_routes.py        # /api/upload, /api/documents, /api/document/<id>
│   ├── health_routes.py          # GET /health
│   └── query_routes.py           # POST /api/query
│
├── utils/
│   ├── __init__.py
│   ├── date_extractor.py         # Regex tanggal (Indo + English, 4 format)
│   ├── file_validator.py         # Validasi ekstensi/ukuran, sanitize_filename
│   ├── logger.py                 # RotatingFileHandler + console
│   ├── response_builder.py       # success_response(), error_response()
│   └── text_cleaner.py           # clean_text(), chunk_text(), count_words()
│
├── templates/                    # Jinja2 HTML (server-rendered)
│   ├── base.html                 # Layout utama + SVG sprites
│   ├── index.html                # Halaman query + upload + scan kamera
│   ├── login.html
│   ├── register.html
│   ├── partials/
│   │   └── sidebar.html          # Sidebar + mobile drawer + desktop collapse
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── documents.html
│   │   └── users.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/
│   ├── css/
│   │   ├── variables.css         # CSS custom properties + base reset
│   │   ├── components.css        # Semua komponen UI (sidebar, form, table, dll)
│   │   └── auth.css              # Layout halaman login/register
│   ├── js/
│   │   └── main.js               # Toast, sidebar drawer, drag-drop upload
│   └── img/
│       └── nade-logo.svg
│
├── docs/                         # Gitbook documentation source
│   ├── concept.md
│   ├── Worklog.md                # Catatan pengerjaan (jangan hapus)
│   ├── DEMO.md                   # Panduan demo dengan 7 dokumen fiktif + 10 pertanyaan
│   ├── getting-started/
│   │   ├── prerequisites.md
│   │   ├── installation.md
│   │   └── CARA-START.md
│   ├── architecture/
│   │   ├── system-overview.md
│   │   ├── data-flow.md
│   │   └── tech-stack.md
│   ├── algorithms/
│   │   └── algorithms.md
│   └── development/
│       └── project-structure.md  (file ini)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # pytest fixtures (app, client, runner)
│   ├── test_app.py               # Flask app + endpoint tests
│   ├── test_config.py            # Konfigurasi & threshold validation
│   └── test_imports.py           # Smoke test semua module
│
├── .github/
│   └── workflows/
│       └── ci.yml                # CI/CD: lint + test + security + build check
│
└── data/                         # ⚠️ Tidak di-commit (.gitignore)
    ├── documents/
    │   └── <user_id>/            # File dokumen per user
    ├── uploads/                  # Temp upload sebelum diproses
    └── app.db                    # SQLite database
```

---

## Konvensi Penting

**Import model SQLAlchemy** — selalu `from models import ...` (bukan dari submodule), agar SQLAlchemy registry ter-load benar sebelum relationship resolution.

**Singleton pattern** — `EmbeddingEngine`, `VectorStore`, `HallucinationChecker` menggunakan `__new__` + `_initialized` flag agar model hanya di-load sekali per proses.

**Chunking** — setiap chunk menjadi satu baris di tabel `documents`. `chunk_index=0` adalah representasi file untuk list/delete UI. Delete satu file = delete semua chunk dengan `filepath` yang sama.

**CSRF** — semua form POST di HTML routes dilindungi `{{ csrf_token() }}`. API blueprints (`/api/*`) tidak butuh CSRF karena menggunakan Bearer token header.
