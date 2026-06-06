# Tech Stack

## Bahasa Pemrograman

| Bahasa | Porsi | Digunakan untuk |
|--------|-------|-----------------|
| Python 3.12+ | ~90% | Backend, core logic, CLI, Flask |
| HTML5 | ~4% | Struktur halaman web |
| CSS3 | ~3% | Styling & responsive design |
| JavaScript (Vanilla) | ~3% | Interaktivitas, fetch API, scan kamera |

---

## Backend

**Flask 3.x** — routing HTTP, HTML server-rendered, API blueprints, CSRF protection (flask-wtf).

**Waitress** — production WSGI server, pure Python, multi-thread (8 threads), tidak butuh nginx.

---

## AI & Machine Learning

### Groq API — `llama-3.1-8b-instant`
LLM utama. Request dikirim ke Groq cloud (GPU mereka).
- Latency: ~400-800ms/request
- Gratis (rate limit per menit)
- Multilingual Indonesia + Inggris
- Tidak butuh GPU lokal

### paraphrase-multilingual-MiniLM-L12-v2
Embedding model multibahasa. Teks → vector 384 dimensi.
- Ukuran: ~471 MB
- Inference: ~5ms (CPU)
- 50+ bahasa termasuk Indonesia
- Berjalan lokal

### mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
NLI model untuk verifikasi halusinasi (two-stage).
- Ukuran: ~560 MB
- Input: (premise=konteks, hypothesis=klaim jawaban)
- Output: entailment / neutral / contradiction probabilities
- Berjalan lokal di CPU (~6-15 detik/query)

---

## Document Processing

### Chunking
```
chunk_size = 300 kata
overlap    = 50 kata
step       = 250 kata

Contoh: PDF 3405 kata → 14 chunks
Similarity sebelum chunking: 0.27
Similarity setelah chunking:  0.64
```

### Format yang Didukung

| Format | Engine |
|--------|--------|
| `.pdf` | pypdf + OCR fallback jika teks < 50 char |
| `.docx` | python-docx (teks + tabel) |
| `.txt` | open() UTF-8 |
| `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` | RapidOCR + pytesseract |

---

## OCR

**RapidOCR** — printed text & handwriting, Python 3.12+ compatible, ~300 MB.

**pytesseract** — supplement OCR, akurat untuk printed text, config: `--oem 3 --psm 6 -l eng+ind`.

**OpenCV** — preprocessing: grayscale → denoise → adaptive threshold.

Sistem pilih hasil terbaik dari keduanya berdasarkan: `score = len(text) × confidence`.

---

## Database

**SQLite via SQLAlchemy 2.0.49**

```sql
users            → id, username, password, email, role, is_active, created_at
documents        → id, user_id, filename, filepath, text, word_count, dates,
                   is_shared, created_at, chunk_index, chunk_total
embeddings_cache → id, doc_id, embedding (JSON), model_name, created_at
query_history    → id, user_id, query_text, answer, sources, confidence,
                   has_conflict, execution_time, created_at
sessions         → id, user_id, token, expires_at, created_at
conflicts_log    → id, query_id, conflict_type, description, affected_docs,
                   severity, created_at
```

---

## Auth & Security

**werkzeug** — PBKDF2 password hashing.

**Session token** — 36-byte random URL-safe token, disimpan di tabel `sessions`, expire 24 jam. Session disimpan di Flask session (server-side via cookie).

**CSRF protection** — flask-wtf pada semua form POST.

---

## Estimasi RAM

```
OS + idle:                  ~2.0 GB
Embedding model (~471MB):   ~0.5 GB
NLI model (~560MB):         ~0.6 GB
Flask + Waitress:           ~0.1 GB
In-memory vector store:     ~0.1 GB
OpenCV + Pillow:            ~0.2 GB
─────────────────────────────────────
Total:                      ~3.5 GB
```

Groq API berjalan di server Groq — **tidak ada beban RAM lokal untuk LLM**.

---

## Latency Observasi (CPU-only, RAM 16GB)

| Tahap | Waktu |
|-------|-------|
| Embed query | ~5ms |
| Similarity search | ~100-500ms |
| Conflict detection | <1ms |
| LLM via Groq API | ~400-800ms |
| LLM via Ollama (CPU) | ~10-90s |
| Hallucination check NLI (CPU) | ~6-15 detik |
| **Total (Groq)** | **~7-16 detik** |
| **Total (Ollama CPU)** | **~20-110 detik** |

NLI berjalan lokal di CPU. Jika ada GPU NVIDIA, tambah `torch` CUDA build → NLI turun ke ~1-2 detik.
