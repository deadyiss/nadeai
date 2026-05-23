# Data Flow

## 1. Upload Document Flow

```
FILE INPUT (PDF/DOCX/TXT)            IMAGE INPUT (foto/scan)
        │                                      │
        ▼                                      ▼
Flask POST /api/upload               Flask POST /api/upload
        │                                      │
        ▼                                      ▼
DocumentProcessor                    OCR Engine
├─ Validate file (ext + size)        ├─ OpenCV preprocess
├─ Extract text                      │   ├─ Grayscale
│   ├─ PDF  → pypdf                  │   ├─ Denoise
│   ├─ DOCX → python-docx            │   └─ Threshold
│   └─ TXT  → open() UTF-8          ├─ RapidOCR (utama)
└─ Clean text                        └─ pytesseract (fallback)
        │                                      │
        └──────────────┬────────────────────────┘
                       ▼
             Text Chunker
       chunk_text(size=300, overlap=50)
       → [chunk_0, chunk_1, ..., chunk_n]
                       │
                       ▼ (per chunk)
              Embedding Engine
    paraphrase-multilingual-MiniLM-L12-v2
    chunk_text → 384-dim normalized vector
                       │
                       ▼
               Vector Store (RAM)
       _vectors[doc_id] = np.ndarray
       _meta[doc_id] = {filename, user_id, ...}
                       │
                       ▼
                 SQLite DB
       INSERT documents (chunk_index, chunk_total)
       INSERT embeddings_cache
```

---

## 2. Query Processing Flow

```
User: "Berapa anggaran proyek SmartCity?"
        │
        ▼
Flask POST /api/query
        │
        ▼
Auth Check (Bearer token valid? role?)
        │
        ▼
Query Processor
        │
        ├─ STEP 1: Embed query → 384-dim vector
        │          ~5ms
        │
        ├─ STEP 2: Similarity Search (Vector Store)
        │   ├─ dot product: query_vec @ all_chunk_vecs
        │   ├─ Filter: chunk user + shared, sim >= 0.15
        │   └─ Return top-K chunks (auto: 3/5/7 by doc count)
        │   ~100-500ms
        │
        ├─ STEP 3: Conflict Detection
        │   ├─ TEMPORAL: beda tanggal antar dokumen → HIGH
        │   ├─ VALUE: beda nilai angka (Rp, %, dll) → HIGH
        │   └─ MULTI_SOURCE: topik dari ≥3 doc high-sim → MEDIUM
        │   <1ms
        │
        ├─ STEP 4: LLM Generation (Groq API)
        │   ├─ System prompt: jawab 1-3 kalimat, cite sumber
        │   ├─ User message: [DOCUMENTS] + [QUESTION]
        │   └─ Model: llama-3.1-8b-instant, temp=0.2, max=300 token
        │   ~400-800ms
        │
        └─ STEP 5: Hallucination Check (NLI, lokal CPU)
            ├─ Extract claims dari jawaban (split kalimat)
            ├─ Per claim:
            │   ├─ Gate: cosine_sim < 0.35 → skip NLI (FLAGGED)
            │   └─ NLI: mDeBERTa(premise=chunk, hypothesis=claim)
            │       ├─ entailment ≥ 0.5 → VERIFIED
            │       ├─ contradiction ≥ 0.5 → FLAGGED
            │       └─ neutral → FLAGGED
            └─ overall_score = 1 - avg(entailment_scores)
            ~6-15 detik (CPU)
        │
        ▼
Confidence Score
  base = avg(chunk similarities)
  score = base × (1 - hallucination_score)
  if has_conflict: score -= 0.2
  clamp(0, 1)
        │
        ▼
INSERT query_history + conflicts_log
        │
        ▼
RESPONSE JSON:
{
  "answer": "...",
  "sources": [...],
  "confidence": 0.72,
  "has_conflict": true,
  "conflict_details": [...],
  "hallucination": {
    "status": "VERIFIED|FLAGGED|NO_CLAIMS",
    "overall_score": 0.12,
    "claims": [...]
  },
  "stages": {
    "search_ms": 210,
    "conflict_ms": 0.5,
    "llm_ms": 513,
    "hallucination_ms": 8200
  }
}
```

---

## 3. Auth Flow

```
REGISTER:
input → validate → hash password (PBKDF2)
     → INSERT users → return success

LOGIN:
input → SELECT user → verify password
     → create token (32-byte hex)
     → INSERT sessions (expires: 24 jam)
     → return token

LOGOUT:
token → DELETE sessions WHERE token = ?

REQUEST AUTH CHECK:
Authorization: Bearer <token>
→ SELECT session WHERE token = ? AND expires_at > now()
→ get user role → proceed / 401
```

---

## 4. Document Chunking

```
Dokumen besar (misal PDF 3000 kata)
        │
        ▼
chunk_text(text, chunk_size=300, overlap=50)
        │
        ▼
┌───────────────────────────────┐
│ chunk_0: kata 0-299           │ → embedding_0 → doc_id=11, chunk_index=0
│ chunk_1: kata 250-549         │ → embedding_1 → doc_id=12, chunk_index=1
│ chunk_2: kata 500-799         │ → embedding_2 → doc_id=13, chunk_index=2
│ ...                           │
│ chunk_13: kata 3000-3299      │ → embedding_13 → doc_id=24, chunk_index=13
└───────────────────────────────┘
        │
        ▼
Query "PHP itu apa?"
→ Retrieve: chunk_7 (sim=0.64) ← berisi definisi PHP
→ Bukan chunk_0 (sim=0.27) ← hanya berisi header dokumen
```
