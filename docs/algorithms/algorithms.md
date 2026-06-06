# Algoritma

## 1. Document Chunking

Dokumen besar dipecah agar setiap bagian dapat di-index secara terpisah.

```
Input:  teks penuh dokumen (bisa ribuan kata)
Output: list chunk ~300 kata dengan overlap 50 kata

step = chunk_size - overlap = 300 - 50 = 250
chunk_i = words[i×250 : i×250 + 300]

Kompleksitas: O(n) dimana n = jumlah kata

Contoh:
  PDF 3405 kata → 14 chunks
  similarity sebelum: 0.27  (satu embedding untuk seluruh dokumen)
  similarity sesudah: 0.64  (embedding per chunk)
```

---

## 2. Similarity Search

Mencari chunk dokumen paling relevan berdasarkan kemiripan semantik dengan query.

```
Formula: cosine_similarity = dot(A, B)
         (A dan B sudah dinormalisasi saat encode → dot = cosine)

Range:   0.0 (tidak relevan) sampai 1.0 (identik)
Threshold minimum: 0.15 (di bawah ini diabaikan)

Top-K otomatis berdasarkan jumlah dokumen:
  ≤ 3 dokumen  → top 3
  4-10 dokumen → top 5
  > 10 dokumen → top 7

Implementasi (NumPy):
  sims = chunk_matrix @ query_vec   # dot product, O(n×d)
  scored = filter(sim >= 0.15)
  top_k = sorted(scored, desc)[:K]

Kompleksitas: O(n×d) dimana n = total chunks, d = 384
```

---

## 3. Conflict Detection

Mendeteksi pertentangan informasi antar dokumen yang di-retrieve.

```
Tipe 1: TEMPORAL_CONFLICT (severity: HIGH)
  Kondisi: ≥2 dokumen berbeda menyebut ≥2 tanggal berbeda
  Contoh: Dok A "1 Januari 2025", Dok B "15 Januari 2025"
  Implementasi: regex ekstrak tanggal → group by doc → compare

Tipe 2: VALUE_CONFLICT (severity: HIGH)
  Kondisi: ≥2 dokumen menyebut angka berbeda untuk tipe nilai yang sama
           dan rasio max/min > 1.1 (selisih > 10%)
  Tipe nilai: currency_rp, currency_usd, percentage, magnitude_id
  Contoh: "Rp 50 juta" vs "Rp 75 juta" → ratio 1.5 > 1.1 → conflict
  Normalisasi: "1.500" → 1500, "50 juta" → 50000000

Tipe 3: MULTI_SOURCE (severity: MEDIUM)
  Kondisi: ≥3 dokumen dengan similarity ≥ 0.5 untuk query yang sama
  Indikasi: topik tersebar di banyak sumber, potensi inkonsistensi

Kompleksitas: O(k×m) dimana k = docs, m = nilai/tanggal per dokumen
```

---

## 4. Hallucination Detection (Two-Stage)

Memverifikasi setiap klaim dalam jawaban AI terhadap dokumen sumber.

```
Mengapa two-stage?
  Cosine similarity saja gagal mendeteksi entity substitution:
    "Ibukota Indonesia adalah Tokyo" vs konteks "...adalah Jakarta"
    similarity = 0.826 → VERIFIED (FALSE NEGATIVE)
  Karena topik sama (ibukota negara) meski fakta berbeda.
  NLI mendeteksi kontradiksi ini dengan benar: contradiction=0.95.

Stage 1 — Cosine Gate (cepat):
  Per klaim:
    embedding(klaim) @ embedding(chunks) → similarities
    if max_similarity < 0.35:
      verdict = "no_context"
      status  = FLAGGED
      skip Stage 2

Stage 2 — NLI Verification (~2-3s per klaim, CPU):
  Model: mDeBERTa-v3-base-xnli-multilingual-nli-2mil7
  Input: premise = chunk_text, hypothesis = klaim
  Output: {entailment, neutral, contradiction} probabilities

  Cek top-2 chunks (TOP_K_CONTEXT_FOR_NLI = 2):
    if entailment >= 0.7: early stop (sudah cukup kuat)

  Decision per klaim:
    contradiction >= 0.5 → FLAGGED (contradiction)
    entailment    >= 0.5 → VERIFIED
    else                 → FLAGGED (neutral/insufficient)

Scoring:
  overall_score = 1 - avg(entailment_scores)
  0.0 = fully verified, 1.0 = fully hallucinated

Kompleksitas: O(c×k) NLI inferences
  c = klaim dalam jawaban (biasanya 1-3)
  k = top-2 context chunks per klaim
```

---

## 5. Confidence Score

```
base = avg(similarity semua chunks yang di-retrieve)

if hallucination.status == NO_CLAIMS (refusal):
  confidence = base                   # tidak ada klaim → tidak ada penalty
else:
  confidence = base × (1 - hallucination_score)

if has_conflict:
  confidence -= 0.2

confidence = clamp(confidence, 0.0, 1.0)

Interpretasi:
  ≥ 0.70  → Tinggi   (jawaban kuat, sumber jelas, tidak ada konflik)
  0.40-0.69 → Sedang (ada ketidakpastian)
  < 0.40  → Rendah   (banyak konflik atau klaim tidak terverifikasi)
  0%      → Sangat rendah (konflik berat + hallucination tinggi)

Catatan: confidence 0% tidak berarti jawaban salah.
Bisa berarti: 4 dokumen berbeda menyebut 4 angka berbeda → penalty -0.2×4
```

---

## 6. Prompt Template

```
SYSTEM:
You are a factual assistant. Answer ONLY using the documents provided.
RULES:
- Answer in the SAME LANGUAGE as the question.
- Be concise: 1-3 sentences maximum. No elaboration, no preamble.
- Cite sources inline like [Document 1].
- Related terms count (e.g. 'anggaran' = 'budget').
- If NO document is relevant, reply exactly:
  "The documents do not contain enough information to answer this."
- NEVER add commentary or knowledge outside the documents.

USER:
=== DOCUMENTS ===
[Document 1: laporan.pdf | relevance=0.64]
<isi chunk>

[Document 2: notulen.docx | relevance=0.58]
<isi chunk>

=== QUESTION ===
<pertanyaan user>
```

Prompt singkat (1-3 kalimat output) mengurangi jumlah klaim → NLI lebih cepat.

---

## 7. Latency Breakdown

```
Hardware referensi: CPU-only, RAM 16GB, tanpa GPU

Tahap                       Waktu
─────────────────────────────────────────────────────
Embed query                 ~5ms
Similarity search           ~100-500ms
Conflict detection          <1ms
LLM via Groq API            ~400-800ms
Hallucination check (NLI)   ~6-15 detik (tergantung panjang jawaban)
─────────────────────────────────────────────────────
Total end-to-end (Groq)     ~7-16 detik
Total end-to-end (Ollama)   ~20-110 detik

Bottleneck: NLI di CPU. Jika GPU NVIDIA tersedia:
  pip install torch --index-url https://download.pytorch.org/whl/cu121
  NLI turun ke ~1-2 detik → total ~2-4 detik
```
