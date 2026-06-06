# System Overview

## Konsep Utama

**RAG (Retrieval-Augmented Generation)** — AI menjawab pertanyaan berdasarkan dokumen yang di-upload, bukan pengetahuan umum. Dilengkapi deteksi konflik antar dokumen dan verifikasi halusinasi per klaim.

---

## Arsitektur

```
┌──────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                         │
│  ┌──────────────────┐        ┌───────────────────────┐  │
│  │   Web Browser    │        │   Terminal (CLI)       │  │
│  │  http://IP:5000  │        │   python3 cli.py       │  │
│  └────────┬─────────┘        └──────────┬─────────────┘  │
└───────────┼──────────────────────────────┼───────────────┘
            │ HTTP (session-based)         │ Direct Python call
            ▼                             ▼
┌──────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                       │
│              Flask + Waitress (0.0.0.0:5000)            │
│   HTML routes  /  API blueprints  /  CSRF protection    │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    CORE LAYER                            │
│                                                          │
│  document_processor → text_cleaner → embedding_engine  │
│         (PDF/DOCX/TXT/OCR)    (chunk 300w/50w)          │
│                                ↓                         │
│                          vector_store                    │
│                    (in-memory NumPy + SQLite)            │
│                                ↓                         │
│         conflict_detector ←──→ query_processor          │
│         (TEMPORAL/VALUE/      (orchestrator pipeline)   │
│          MULTI_SOURCE)                ↓                  │
│                          llm_engine (Groq API)           │
│                                ↓                         │
│                    hallucination_checker                 │
│                    (cosine gate + NLI mDeBERTa)          │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    DATA LAYER                            │
│  SQLite (app.db)                   File System           │
│  ├─ users                          data/documents/       │
│  ├─ documents (per chunk)          └─ <user_id>/         │
│  ├─ embeddings_cache               data/uploads/ (temp) │
│  ├─ query_history                                        │
│  ├─ sessions                                             │
│  └─ conflicts_log                                        │
└─────────────────────────┬────────────────────────────────┘
                          │ (keluar ke internet)
                          ▼
┌──────────────────────────────────────────────────────────┐
│               EXTERNAL SERVICES                          │
│  Groq API (api.groq.com) — llama-3.1-8b-instant         │
│  HuggingFace (download model, sekali saja)               │
└──────────────────────────────────────────────────────────┘
```

---

## Multi-User & Role

| Fitur | Admin | User |
|-------|-------|------|
| Upload dokumen pribadi | ✓ | ✓ |
| Upload dokumen shared | ✓ | ✗ |
| Query dokumen | ✓ | ✓ |
| Lihat dokumen shared | ✓ | ✓ |
| Lihat dokumen user lain | ✓ | ✗ |
| Hapus dokumen manapun | ✓ | ✗ |
| Manage users | ✓ | ✗ |
| Monitor query history | ✓ | ✗ |
| CLI (bypass auth) | berjalan sebagai admin | — |

---

## Network Setup

```
         WiFi Router / LAN
              │
   ┌──────────┼──────────┐
   │          │          │
┌──┴───┐  ┌──┴───┐  ┌───┴──┐
│SERVER│  │CLIENT│  │CLIENT│
│:5000 │  │ HP   │  │Tablet│
└──────┘  └──────┘  └──────┘

Server: python3 app.py (bind 0.0.0.0:5000)
Client: http://<IP_SERVER>:5000
```

---

## Status Fitur

| Fitur | Status |
|-------|--------|
| Upload PDF/DOCX/TXT | ✅ Selesai |
| Upload gambar + OCR | ✅ Selesai |
| Multi-page camera scan | ✅ Selesai |
| Document chunking | ✅ Selesai |
| Similarity search (cosine) | ✅ Selesai |
| Conflict detection (3 tipe) | ✅ Selesai |
| Hallucination check (NLI) | ✅ Selesai |
| Groq API integration | ✅ Selesai |
| Ollama fallback | ✅ Selesai |
| Multi-user + auth | ✅ Selesai |
| Admin dashboard | ✅ Selesai |
| CLI | ✅ Selesai |
| GitHub Actions CI/CD | ✅ Selesai |
| Formal test suite | ✅ Selesai (Phase 7) |
