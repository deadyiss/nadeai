# Konsep Aplikasi

## Apa Ini?

**RAG System** — sistem tanya-jawab cerdas berbasis dokumen. User upload dokumen, lalu bisa bertanya tentang isi dokumen tersebut. AI menjawab hanya berdasarkan dokumen yang di-upload, bukan dari pengetahuan umum.

---

## Masalah yang Diselesaikan

| Masalah | Solusi |
|---------|--------|
| AI tidak tahu isi dokumen pribadi | RAG: jawaban hanya dari dokumen yang di-upload |
| AI bisa mengarang fakta (halusinasi) | NLI Hallucination Detection: setiap klaim diverifikasi |
| Tidak tahu ada konflik antar dokumen | Conflict Detection: deteksi perbedaan nilai/tanggal otomatis |
| Dokumen besar hanya terbaca sebagian | Chunking: dokumen dipecah, seluruh isi dapat di-index |
| Hanya baca file digital | OCR: bisa baca foto & scan dokumen |
| Single user | Multi-user dengan role Admin & User |

---

## Cara Kerja

```
1. User upload dokumen (PDF, DOCX, TXT, atau foto)
2. Sistem ekstrak teks (OCR jika foto/scan)
3. Teks dipecah jadi chunk 300 kata
4. Setiap chunk diubah jadi vector embedding (384 angka)
5. User ketik pertanyaan
6. Pertanyaan diubah jadi vector yang sama
7. Sistem cari chunk paling mirip (cosine similarity)
8. Cek: ada dokumen yang saling bertentangan?
9. Chunk relevan dikirim ke Groq API → AI buat jawaban
10. NLI model verifikasi: apakah klaim ada di dokumen?
11. User terima: jawaban + sumber + confidence + status konflik
```

---

## Perbandingan vs ChatGPT Biasa

| Aspek | ChatGPT | Sistem Ini |
|-------|---------|------------|
| Dokumen pribadi | Tidak bisa | Upload & tanya langsung |
| Halusinasi | Tidak dicek | Diverifikasi dengan NLI |
| Konflik dokumen | Tidak tahu | Terdeteksi otomatis |
| Dokumen besar | Terbatas | Chunking — baca semua |
| Input foto/scan | Terbatas | OCR multibahasa |
| Multi-user | - | Admin + User roles |

---

## Stack Ringkas

```
OS:          Ubuntu 26.04 LTS
Python:      3.14
LLM:         llama-3.1-8b-instant via Groq API (~400-800ms/query)
Embedding:   paraphrase-multilingual-MiniLM-L12-v2 (384 dim)
NLI:         mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 (CPU)
OCR:         RapidOCR + pytesseract + OpenCV
Backend:     Flask + Waitress
Database:    SQLite
Frontend:    HTML + CSS + JavaScript (Vanilla)
RAM usage:   ~2.5 GB
```

---

## Arsitektur Pipeline Query

```
Pertanyaan User
      │
      ▼
 Embed Query (384-dim vector)
      │
      ▼
 Similarity Search → Top-K chunks relevan
      │
      ▼
 Conflict Detection → TEMPORAL / VALUE / MULTI_SOURCE
      │
      ▼
 Groq API (llama-3.1-8b-instant) → Jawaban
      │
      ▼
 NLI Hallucination Check → VERIFIED / FLAGGED
      │
      ▼
 Response: jawaban + sumber + confidence + konflik
```
