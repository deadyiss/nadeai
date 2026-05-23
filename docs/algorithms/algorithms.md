# Algoritma

## 1. Document Chunking

Dokumen besar dipecah agar setiap bagian dapat di-index secara terpisah.

```
Input:  teks penuh dokumen (bisa ribuan kata)
Output: list chunk teks ~300 kata dengan overlap 50 kata

Formula:
  step = chunk_size - overlap = 300 - 50 = 250
  chunk_i = words[i*250 : i*250 + 300]

Contoh:
  PDF 3405 kata → 14 chunks
  Setiap chunk dapat embedding sendiri → retrieval presisi
```

**Kompleksitas:** O(n) dimana n = jumlah kata

---

## 2. Similarity Search

Mencari chunk dokumen paling relevan berdasarkan kemiripan makna dengan query.

```
Formula: cosine_similarity = dot(A, B)
         (A dan B sudah dinormalisasi → dot product = cosine sim)

Range:   -1 (berbeda total) sampai 1 (identik)
Min threshold: 0.15 (chunk di bawah ini diabaikan)
Top-K:   otomatis berdasarkan jumlah dokumen
         ≤3 file  → top 3
         4-10 file → top 5
         >10 file  → top 7
```

**Kompleksitas:** O(n) dimana n = jumlah chunk di memory

---

## 3. Conflict Detection

Mendeteksi pertentangan informasi antar dokumen yang di-retrieve.

```
Tipe Konflik:
├─ TEMPORAL_CONFLICT  → dokumen berbeda menyebut tanggal berbeda
│   Severity: HIGH
│   Contoh: dok A sebut "1 Januari 2025", dok B sebut "15 Januari 2025"
│
├─ VALUE_CONFLICT     → dokumen berbeda menyebut nilai angka berbeda
│   Severity: HIGH
│   Contoh: dok A "Rp 50 juta", dok B "Rp 75 juta", dok C "Rp 85 juta"
│   Threshold: perbedaan > 10% (ratio max/min > 1.1)
│
└─ MULTI_SOURCE       → topik muncul di ≥3 dokumen dengan sim ≥ 0.5
    Severity: MEDIUM
    Indikasi: potensi inkonsistensi meski tidak langsung bertentangan

Flow:
Retrieved chunks → group by doc
               → extract dates (regex)
               → extract values (Rp, $, %, jumlah)
               → compare across docs
               → return conflicts sorted: HIGH → MEDIUM
```

**Kompleksitas:** O(k × m) dimana k = docs, m = nilai per dokumen

---

## 4. Hallucination Detection (Two-Stage)

Memverifikasi setiap klaim dalam jawaban AI terhadap dokumen sumber.

```
Stage 1 — Cosine Gate (cepat, O(c×k)):
  Per klaim:
    hitung cosine_similarity(klaim, tiap chunk)
    jika max_similarity < 0.35 → FLAGGED (no_context), skip Stage 2

Stage 2 — NLI Verification (presisi, ~2-3s per klaim):
  Model: mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
  Input: (premise=chunk_teks, hypothesis=klaim)
  Output: {entailment, neutral, contradiction} probabilities

  Decision per klaim:
    contradiction ≥ 0.5 → FLAGGED (contradiction)
    entailment    ≥ 0.5 → VERIFIED
    else                → FLAGGED (neutral/insufficient)

  Early stop: jika entailment ≥ 0.7, tidak perlu cek chunk lain

Scoring:
  overall_score = 1 - avg(entailment_per_klaim)
  0.0 = fully verified, 1.0 = fully hallucinated
```

**Mengapa dua stage?**
Cosine similarity saja tidak cukup — ia mengukur topik, bukan kebenaran fakta.
Contoh: "Ibukota Indonesia adalah Tokyo" memiliki similarity tinggi dengan
"Ibukota Indonesia adalah Jakarta" karena topiknya sama (ibukota negara),
padahal faktanya salah. NLI mendeteksi kontradiksi ini.

**Kompleksitas:** O(c × k) NLI inferences; c = klaim, k = top-2 chunk per klaim

---

## 5. Confidence Score

```
base = avg(similarity semua chunk yang di-retrieve)
score = base × (1 - hallucination_score)
if has_conflict: score -= 0.2
confidence = clamp(score, 0.0, 1.0)

Interpretasi:
  ≥ 0.70 → Tinggi  (jawaban kuat, sumber jelas)
  0.40-0.69 → Sedang (ada ketidakpastian)
  < 0.40 → Rendah  (perlu verifikasi manual)
  0%     → Sangat rendah (konflik banyak + klaim tidak terverifikasi)
```

---

## 6. Prompt Template (LLM)

```
SYSTEM:
You are a factual assistant. Answer ONLY using the documents provided.
RULES:
- Answer in the SAME LANGUAGE as the question.
- Be concise: 1-3 sentences maximum. No elaboration, no preamble.
- Cite sources inline like [Document 1].
- Related terms count as a match (e.g. 'anggaran' = 'budget').
- If NO document is relevant, reply exactly:
  "The documents do not contain enough information to answer this."
- NEVER add commentary or knowledge outside the documents.

USER:
=== DOCUMENTS ===
[Document 1: filename.pdf | relevance=0.64]
<chunk teks>

[Document 2: laporan.docx | relevance=0.58]
<chunk teks>

=== QUESTION ===
<pertanyaan user>
```

---

## 7. Timing Observasi (Hardware: CPU only, RAM 16GB)

```
Embed query:                 ~5ms
Similarity search:           ~100-500ms
Conflict detection:          <1ms
LLM via Groq API:            ~400-800ms
Hallucination check (NLI):   ~6-15 detik (CPU)
─────────────────────────────────────────
Total end-to-end:            ~7-16 detik
```
