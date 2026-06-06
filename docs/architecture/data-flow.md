# Data Flow

## 1. Upload Dokumen

```
FILE (PDF/DOCX/TXT)              IMAGE (foto/scan)
        │                                │
        ▼                                ▼
Flask POST /upload               Flask POST /upload
        │                                │
        ▼                                ▼
FileValidator                    OCREngine
├─ Cek ekstensi + ukuran         ├─ OpenCV preprocess
└─ Sanitize filename             │   └─ grayscale → denoise → threshold
        │                        ├─ RapidOCR (handwriting-friendly)
        ▼                        └─ pytesseract (printed text)
DocumentProcessor                       │ pilih score terbaik
├─ PDF  → pypdf                         │
│   └─ fallback OCR jika < 50 char      │
├─ DOCX → python-docx                   │
└─ TXT  → open() UTF-8                  │
        │                               │
        └──────────────┬────────────────┘
                       ▼
             text_cleaner.clean_text()
                       │
                       ▼
             chunk_text(size=300, overlap=50)
             → [chunk_0, chunk_1, ..., chunk_n]
                       │
              (per chunk, loop)
                       │
                       ▼
             EmbeddingEngine.encode(chunk)
             → 384-dim normalized float32 vector
                       │
                       ▼
             VectorStore.add(doc, session)
             ├─ _vectors[doc_id] = vec (RAM)
             ├─ _meta[doc_id] = {...}
             └─ INSERT embeddings_cache (SQLite)
                       │
                       ▼
             INSERT documents (SQLite)
             chunk_index=i, chunk_total=n
```

---

## 2. Query Pipeline

```
User input: "Berapa anggaran proyek SmartCity?"
        │
        ▼
Flask POST /  (HTML form) atau POST /api/query (JSON API)
        │
        ▼
Auth check (session token valid? expired?)
        │
        ▼
QueryProcessor.process(query, user_id, include_shared)
        │
        ├─ [1] EMBED QUERY                    ~5ms
        │      EmbeddingEngine.encode(query)
        │      → 384-dim vector
        │
        ├─ [2] SIMILARITY SEARCH              ~100-500ms
        │      VectorStore.search(query_vec)
        │      ├─ Filter: user docs + shared docs
        │      ├─ dot product: query_vec @ chunk_matrix
        │      ├─ Filter: sim >= 0.15 (SIMILARITY_MIN_THRESHOLD)
        │      └─ Top-K: auto (≤3 docs→3, 4-10→5, >10→7)
        │
        ├─ [3] CONFLICT DETECTION             <1ms
        │      ConflictDetector.detect(hits)
        │      ├─ TEMPORAL_CONFLICT: beda tanggal antar dok → HIGH
        │      ├─ VALUE_CONFLICT: beda angka > 10% → HIGH
        │      └─ MULTI_SOURCE: ≥3 dok sim ≥ 0.5 → MEDIUM
        │
        ├─ [4] LLM GENERATION                 ~400-800ms (Groq)
        │      LLMEngine.answer(query, context_chunks)
        │      ├─ Build prompt: system + [DOCUMENTS] + [QUESTION]
        │      └─ llama-3.1-8b-instant, temp=0.2, max_tokens=300
        │
        └─ [5] HALLUCINATION CHECK            ~6-15s (NLI CPU)
               HallucinationChecker.check(answer, chunks)
               ├─ Extract claims (split kalimat)
               └─ Per claim:
                   ├─ Gate: sim < 0.35 → FLAGGED (no_context), skip NLI
                   └─ NLI: mDeBERTa(premise=chunk, hypothesis=claim)
                       ├─ entailment ≥ 0.5  → VERIFIED
                       ├─ contradiction ≥ 0.5 → FLAGGED
                       └─ neutral           → FLAGGED
        │
        ▼
Confidence Score
  base = avg(chunk similarities)
  score = base × (1 - hallucination_score)
  if has_conflict: score -= 0.2
  clamp(0.0, 1.0)
        │
        ▼
INSERT query_history + conflicts_log (SQLite)
        │
        ▼
Response (JSON atau HTML template):
{
  answer, sources, confidence, has_conflict,
  conflict_details, hallucination, execution_time_ms, stages
}
```

---

## 3. Auth Flow

```
REGISTER:
POST /register → validate → hash password (PBKDF2)
              → INSERT users → flash success → redirect /login

LOGIN:
POST /login → SELECT user → check_password_hash
           → INSERT sessions (token, expires_at = now+24h)
           → session["token"] = token → redirect /

LOGOUT:
GET /logout → DELETE sessions WHERE token = ?
           → session.clear() → redirect /login

REQUEST (setiap halaman protected):
Cookie session["token"]
→ SELECT session WHERE token = ? AND expires_at > now()
→ SELECT user → CurrentUser object → inject ke template / route
```

---

## 4. Document Chunking

```
PDF 3405 kata
        │
        ▼
chunk_text(text, chunk_size=300, overlap=50)
step = 300 - 50 = 250

┌─────────────────────────────────────┐
│ chunk_0 : kata 0   - 299            │ → doc_id=11, chunk_index=0
│ chunk_1 : kata 250 - 549            │ → doc_id=12, chunk_index=1
│ chunk_2 : kata 500 - 799            │ → doc_id=13, chunk_index=2
│ ...                                 │
│ chunk_13: kata 3250 - 3405          │ → doc_id=24, chunk_index=13
└─────────────────────────────────────┘
        │
        ▼ Query: "PHP itu apa?"
Retrieve chunk_7 (sim=0.64) ← berisi definisi PHP di tengah dokumen
vs sebelumnya chunk_0 (sim=0.27) ← hanya header
```
