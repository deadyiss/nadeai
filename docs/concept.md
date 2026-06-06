# Konsep Aplikasi

## Apa Ini?

**Nade AI** adalah sistem tanya-jawab cerdas berbasis dokumen. User upload dokumen, lalu bisa bertanya tentang isi dokumen tersebut. AI menjawab **hanya** berdasarkan dokumen yang di-upload, bukan dari pengetahuan umum AI.

---

## Masalah yang Diselesaikan

| Masalah | Solusi |
|---------|--------|
| AI tidak tahu isi dokumen pribadi | RAG: jawaban hanya dari dokumen yang di-upload |
| AI bisa mengarang fakta (halusinasi) | Two-stage NLI Hallucination Detection: setiap klaim diverifikasi |
| Tidak tahu ada konflik antar dokumen | Conflict Detection: deteksi perbedaan nilai/tanggal otomatis |
| Dokumen besar hanya terbaca sebagian | Chunking (300 kata, overlap 50): seluruh isi ter-index |
| Hanya baca file digital | OCR: bisa baca foto & scan dokumen tercetak maupun tulisan tangan |
| Single user | Multi-user: role Admin & User, dokumen shared/private |
| LLM lokal terlalu lambat di CPU | Groq API: ~400-800ms, gratis, multilingual |

---

## Cara Kerja

```
1. User upload dokumen (PDF, DOCX, TXT, atau foto)
2. Sistem ekstrak teks (OCR jika foto/scan)
3. Teks dipecah jadi chunk 300 kata dengan overlap 50 kata
4. Setiap chunk diubah jadi vector embedding (384 dimensi)
5. User ketik pertanyaan
6. Pertanyaan diubah jadi vector yang sama
7. Sistem cari chunk paling mirip (cosine similarity)
8. Cek: ada dokumen yang saling bertentangan? (conflict detection)
9. Chunk relevan dikirim ke Groq API → AI buat jawaban 1-3 kalimat
10. NLI model verifikasi: apakah klaim ada di dokumen? (hallucination check)
11. User terima: jawaban + sumber + confidence score + status konflik
```

---

## Perbandingan vs ChatGPT Biasa

| Aspek | ChatGPT | Nade AI |
|-------|---------|---------|
| Dokumen pribadi | Tidak bisa | Upload & tanya langsung |
| Halusinasi | Tidak dicek | Diverifikasi per klaim (NLI) |
| Konflik dokumen | Tidak tahu | Terdeteksi otomatis (3 tipe) |
| Dokumen besar | Terbatas | Chunking — baca semua |
| Input foto/scan | Terbatas | OCR multibahasa |
| Multi-user | Tidak | Admin + User + shared docs |
| Privacy | Data ke server OpenAI | Berjalan lokal di jaringan sendiri |

---

## Stack Ringkas

```
OS:          Ubuntu 22.04+ / Windows (Python 3.12+)
Python:      3.12 (Windows) / 3.14 (Linux)
LLM:         llama-3.1-8b-instant via Groq API (~400-800ms/query)
Embedding:   paraphrase-multilingual-MiniLM-L12-v2 (384 dim, ~471MB)
NLI:         mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 (~560MB, CPU)
OCR:         RapidOCR + pytesseract + OpenCV
Backend:     Flask + Waitress
Database:    SQLite via SQLAlchemy 2.0.49
Frontend:    HTML + CSS + JavaScript (Vanilla)
RAM usage:   ~3.5 GB (tanpa GPU)
```

---

## Arsitektur Pipeline Query

```
Pertanyaan User
      │
      ▼
 Embed Query (384-dim vector, ~5ms)
      │
      ▼
 Similarity Search → Top-K chunks relevan (~100-500ms)
      │
      ▼
 Conflict Detection → TEMPORAL / VALUE / MULTI_SOURCE (<1ms)
      │
      ▼
 Groq API (llama-3.1-8b-instant) → Jawaban 1-3 kalimat (~400-800ms)
      │
      ▼
 NLI Hallucination Check (mDeBERTa, CPU) → VERIFIED / FLAGGED (~6-15s)
      │
      ▼
 Confidence Score = base_sim × (1 - hallucination_score) - 0.2×conflict
      │
      ▼
 Response: jawaban + sumber + confidence + konflik + timing
```
