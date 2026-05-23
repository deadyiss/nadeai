# Prerequisites

## Hardware

| Komponen | Minimum | Keterangan |
|----------|---------|------------|
| RAM | 8 GB | NLI model ~560MB, embedding ~471MB |
| Storage | 5 GB | Dependencies + models |
| OS | Ubuntu 22.04+ / Debian | Atau distro Linux lain |
| Internet | Diperlukan | Untuk Groq API & download model pertama kali |

> **Catatan:** Tidak butuh GPU. Semua berjalan di CPU.

---

## Groq API Key (Wajib)

Sistem menggunakan Groq API sebagai LLM engine (gratis, cepat ~400-800ms).

1. Buka [console.groq.com](https://console.groq.com)
2. Sign up / Login (bisa dengan akun Google)
3. Klik **API Keys** → **Create API Key**
4. Copy API key (format: `gsk_...`)
5. Simpan di file `.env` (lihat bagian Instalasi)

---

## System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  git \
  tesseract-ocr \
  tesseract-ocr-ind \
  tesseract-ocr-eng \
  libgl1 \
  libglib2.0-0t64 \
  libsm6 \
  libxrender1 \
  libxext6
```

---

## Verifikasi

```bash
python3 --version     # Python 3.10+ (ideal 3.14)
tesseract --version   # tesseract 5.x
```

---

## Model yang Di-download Otomatis

Saat pertama kali menjalankan aplikasi, dua model akan otomatis diunduh:

| Model | Ukuran | Fungsi |
|-------|--------|--------|
| `paraphrase-multilingual-MiniLM-L12-v2` | ~471 MB | Embedding teks → vector |
| `mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | ~560 MB | Verifikasi halusinasi (NLI) |

Download hanya terjadi sekali, kemudian tersimpan di cache lokal (`~/.cache/huggingface/`).
