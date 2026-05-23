# System Overview

## Konsep Utama

**RAG System (Retrieval-Augmented Generation)** — sistem tanya-jawab yang menjawab pertanyaan user berdasarkan dokumen yang mereka unggah, bukan dari pengetahuan umum AI.

---

## Analogi Sederhana

```
User upload 4 laporan proyek
       ↓
Sistem "membaca" dan "mengingat" semua dokumen (chunking + embedding)
       ↓
User tanya: "Berapa anggaran proyek SmartCity?"
       ↓
Sistem cari chunk dokumen paling relevan
       ↓
Cek: ada informasi yang saling bertentangan?
       ↓
Groq API (llama-3.1-8b-instant) buat jawaban dari chunk tersebut
       ↓
NLI model verifikasi: apakah klaim ada di dokumen?
       ↓
User terima: jawaban + sumber + confidence + status konflik
```

---

## Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                         │
│  ┌──────────────────┐        ┌───────────────────────┐  │
│  │   Web Browser    │        │   Terminal (CLI)       │  │
│  │  http://IP:5000  │        │   python3 cli.py       │  │
│  └────────┬─────────┘        └──────────┬─────────────┘  │
└───────────┼──────────────────────────────┼───────────────┘
            │ HTTP                         │ Direct Call
            ▼                             ▼
┌──────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                       │
│              Flask Web Server (Waitress)                 │
│   POST /api/upload     POST /api/query                   │
│   POST /auth/login     POST /auth/register               │
│   GET  /api/documents  GET  /admin/dashboard             │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    CORE LAYER                            │
│                                                          │
│  Document Processor → Text Chunker → Embedding Engine   │
│                                ↓                         │
│                          Vector Store                    │
│                                ↓                         │
│         Conflict Detector ←──→ Hallucination Checker    │
│                                ↓                         │
│                          LLM Engine                      │
│                    (Groq API — cloud)                    │
└─────────────────────────┬────────────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────┐
│                    DATA LAYER                            │
│  SQLite DB                       File System             │
│  ├─ users                        data/documents/         │
│  ├─ documents (per chunk)        └─ <user_id>/           │
│  ├─ embeddings_cache             data/uploads/           │
│  ├─ query_history                                        │
│  ├─ sessions                                             │
│  └─ conflicts_log                                        │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼ (keluar ke internet)
┌──────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                       │
│   Groq API (api.groq.com)                               │
│   Model: llama-3.1-8b-instant                           │
│   Latency: ~400-800ms/request                           │
└──────────────────────────────────────────────────────────┘
```

---

## Multi-User & Role System

| Fitur | Admin | User |
|-------|-------|------|
| Upload dokumen pribadi | ✓ | ✓ |
| Upload dokumen shared | ✓ | ✗ |
| Query dokumen | ✓ | ✓ |
| Lihat dokumen shared | ✓ | ✓ |
| Lihat dokumen user lain | ✓ | ✗ |
| Hapus dokumen manapun | ✓ | ✗ |
| Manage users | ✓ | ✗ |
| Monitor sistem | ✓ | ✗ |
| Lihat semua query history | ✓ | ✗ |

---

## LAN Network Setup

```
          WiFi Router / LAN
               │
    ┌──────────┼──────────┐
    │          │          │
┌───┴───┐  ┌──┴───┐  ┌───┴──┐
│Laptop │  │  HP  │  │ Tab  │
│SERVER │  │CLIENT│  │CLIENT│
│:5000  │  │:5000 │  │:5000 │
└───────┘  └──────┘  └──────┘

Laptop menjalankan python3 app.py
Perangkat lain akses http://<IP_LAPTOP>:5000
```
