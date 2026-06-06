# Prerequisites

## Hardware

| Komponen | Minimum | Keterangan |
|----------|---------|------------|
| RAM | 8 GB | NLI ~560MB + embedding ~471MB + OS overhead |
| Storage | 5 GB | Dependencies + model cache + dokumen |
| OS | Ubuntu 22.04+ / Windows 10+ | Lihat bagian OS di bawah |
| Internet | Diperlukan | Untuk Groq API & download model pertama kali |
| GPU | Tidak wajib | CPU-only berjalan, NLI ~6-15s/query |

---

## Groq API Key (Wajib)

LLM engine menggunakan Groq API — gratis, ~400-800ms per query.

1. Buka [console.groq.com](https://console.groq.com)
2. Sign up / Login (bisa dengan Google)
3. Klik **API Keys** → **Create API Key**
4. Copy key (format: `gsk_...`)
5. Masukkan ke file `.env`: `GROQ_API_KEY=gsk_xxx`

---

## Platform yang Didukung

### Linux (Ubuntu 22.04 / 24.04 / 26.04)

Python yang digunakan: `python3` bawaan sistem (3.10+). Ubuntu 26.04 sudah Python 3.14 — kompatibel.

System dependencies yang dibutuhkan:
```bash
sudo apt install -y \
  python3 python3-venv python3-pip git \
  tesseract-ocr tesseract-ocr-ind tesseract-ocr-eng \
  libgl1 libglib2.0-0t64 libsm6 libxrender1 libxext6
```

### Windows 10 / 11

Python yang digunakan: **Python 3.12** (3.14 belum ada wheel untuk numpy/Pillow di Windows).
Tesseract: install manual dari https://github.com/UB-Mannheim/tesseract/wiki

---

## Model yang Di-download Otomatis

Saat pertama kali `python app.py` dijalankan, dua model diunduh dari HuggingFace:

| Model | Ukuran | Fungsi |
|-------|--------|--------|
| `paraphrase-multilingual-MiniLM-L12-v2` | ~471 MB | Teks → vector embedding |
| `mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | ~560 MB | Verifikasi halusinasi (NLI) |

Download hanya sekali, tersimpan di `~/.cache/huggingface/`. Boot berikutnya langsung dari cache.

Boot pertama: ~15-20 detik. Boot berikutnya: ~5 detik.

---

## Ollama (Opsional)

Jika ingin LLM berjalan offline tanpa Groq API:

| Platform | Cara Install |
|----------|-------------|
| Linux (Ubuntu) | `sudo snap install ollama` (Ubuntu 26.04) atau `curl -fsSL https://ollama.com/install.sh \| sh` |
| Windows | Download installer dari https://ollama.com/download/windows |

Setelah install: `ollama pull llama3.1:8b`

> Catatan: LLM lokal di CPU **sangat lambat** (~25-90 detik/query). Groq API sangat direkomendasikan kecuali tidak ada akses internet.
