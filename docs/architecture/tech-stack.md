# Tech Stack Detail

## Bahasa Pemrograman

| Bahasa | Porsi | Digunakan Untuk |
|--------|-------|-----------------|
| Python 3.14 | ~90% | Backend, core logic, CLI, Flask |
| HTML5 | ~4% | Struktur halaman web |
| CSS3 | ~3% | Styling & responsive design |
| JavaScript (Vanilla) | ~3% | Interaktivitas web, fetch API |

---

## Backend

### Flask 3.x
Lightweight web framework. Routing HTTP, serving HTML, API endpoints.

### Waitress
Production WSGI server. Pure Python, support Python 3.14, cocok untuk LAN multi-user.

---

## AI & Machine Learning

### Groq API — `llama-3.1-8b-instant`
LLM engine utama. Request dikirim ke Groq cloud, diproses di GPU mereka.
- Latency: ~400-800ms per request
- Gratis (dengan rate limit)
- Tidak perlu GPU lokal
- Multilingual (Indonesia + Inggris)

### paraphrase-multilingual-MiniLM-L12-v2
Model embedding multibahasa. Mengubah teks → vector 384 dimensi.
- Ukuran: ~471MB
- Inference: ~5ms
- Berjalan lokal (CPU)
- Support 50+ bahasa termasuk Indonesia

### mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
Model NLI (Natural Language Inference) untuk verifikasi halusinasi.
- Ukuran: ~560MB
- Input: (premise=konteks dokumen, hypothesis=klaim jawaban AI)
- Output: probabilitas entailment / neutral / contradiction
- Berjalan lokal di CPU (~6-15 detik per query)

---

## Document Processing

### Document Chunking
Dokumen besar dipecah menjadi chunk 300 kata dengan overlap 50 kata.
- Setiap chunk mendapat embedding sendiri
- Memungkinkan retrieval presisi dari dokumen panjang
- Implementasi: `utils/text_cleaner.chunk_text()`

### Format yang Didukung
| Format | Engine |
|--------|--------|
| PDF | pypdf |
| DOCX | python-docx |
| TXT | built-in open() |
| JPG, PNG, BMP, TIFF | RapidOCR + pytesseract |

---

## OCR

### RapidOCR
- Support printed text & handwriting
- Python 3.14 compatible
- Ringan (~300MB)

### pytesseract
OCR supplement. Akurat untuk printed text. Config: `--oem 3 --psm 6 -l eng+ind`

### OpenCV
Image preprocessing sebelum OCR: grayscale, denoise, threshold, deskew.

---

## Vector Operations

### NumPy
Cosine similarity via dot product pada normalized vectors. `sims = matrix @ query_vec`

---

## Database

### SQLite via SQLAlchemy 2.0.49
- SQLite: built-in Python, file tunggal, zero configuration
- Cukup untuk skala kecil hingga menengah

#### Schema

```sql
users            → id, username, password, email, role, is_active, created_at
documents        → id, user_id, filename, filepath, text, word_count, dates,
                   is_shared, created_at, chunk_index, chunk_total
embeddings_cache → id, doc_id, embedding, model_name, created_at
query_history    → id, user_id, query_text, answer, sources, confidence,
                   has_conflict, execution_time, created_at
sessions         → id, user_id, token, expires_at, created_at
conflicts_log    → id, query_id, conflict_type, description, affected_docs,
                   severity, created_at
```

---

## Auth & Security

### werkzeug
Password hashing dengan PBKDF2: `generate_password_hash`, `check_password_hash`.

### Session Token
Token Bearer di header `Authorization`. Disimpan di tabel `sessions`, expire 24 jam.

---

## RAM Usage (Estimasi)

```
OS Ubuntu 26.04:              ~2.0 GB
Embedding model (~471MB):     ~0.5 GB
NLI model (~560MB):           ~0.6 GB
Flask + Waitress:             ~0.1 GB
In-memory vector store:       ~0.1 GB
OpenCV + Pillow:              ~0.2 GB
─────────────────────────────────────
TOTAL:                        ~3.5 GB
```

> Groq API berjalan di server Groq — tidak ada beban RAM lokal untuk LLM.

---

## Network

```
Flask Host:    0.0.0.0 (listen semua interface)
Flask Port:    5000
Groq API:      api.groq.com (HTTPS, butuh internet)
LAN Access:    http://<IP_LAPTOP>:5000
```
