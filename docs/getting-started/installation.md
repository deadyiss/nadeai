# Instalasi

Pilih platform:
- [Linux (Ubuntu)](#linux)
- [Windows](#windows)

---

## Linux

### 1. System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3 python3-venv python3-pip git \
  tesseract-ocr tesseract-ocr-ind tesseract-ocr-eng \
  libgl1 libglib2.0-0t64 libsm6 libxrender1 libxext6
```

### 2. Clone & Masuk Direktori

```bash
git clone <repo-url>
cd nadeai
```

### 3. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Konfigurasi .env

```bash
cp .env.example .env
nano .env
```

Wajib diisi:
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
SECRET_KEY=ganti-dengan-string-acak-minimal-32-karakter
```

### 6. Buat Folder & Init Database

```bash
mkdir -p data/{documents,uploads} logs
python3 -c "from models.database import init_db; init_db()"
```

Output: `Database initialized successfully.`

### 7. Jalankan

```bash
python3 app.py
```

Buka browser: `http://localhost:5000` — login `admin` / `admin123`

---

## Windows

### 1. Install Python 3.12

Download: https://www.python.org/downloads/release/python-3120/

Pilih **Windows installer (64-bit)**. Centang **Add Python to PATH** saat install.

Verifikasi:
```powershell
python --version
# Python 3.12.x
```

### 2. Install Tesseract OCR

Download: https://github.com/UB-Mannheim/tesseract/wiki

Pilih versi terbaru 64-bit. Saat install centang **Indonesian** dan **English**. Catat path install (default: `C:\Program Files\Tesseract-OCR\`).

Tambahkan ke PATH jika belum otomatis:
```
System Properties → Environment Variables → Path → New:
C:\Program Files\Tesseract-OCR\
```

Verifikasi: `tesseract --version`

### 3. Clone & Masuk Direktori

```powershell
git clone <repo-url>
cd nadeai
```

### 4. Virtual Environment

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

Jika error ExecutionPolicy:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 5. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 6. Konfigurasi .env

```powershell
copy .env.example .env
notepad .env
```

Wajib diisi:
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
SECRET_KEY=ganti-dengan-string-acak-minimal-32-karakter
```

### 7. Buat Folder & Init Database

```powershell
mkdir data\documents, data\uploads, logs
python -c "from models.database import init_db; init_db()"
```

Output: `Database initialized successfully.`

### 8. Jalankan

```powershell
python app.py
```

Buka browser: `http://localhost:5000` — login `admin` / `admin123`

---

## Verifikasi Instalasi

```bash
# Linux
python3 -c "import config; print('LLM:', config.LLM_PROVIDER, config.LLM_MODEL)"

# Windows
python -c "import config; print('LLM:', config.LLM_PROVIDER, config.LLM_MODEL)"
```

Output: `LLM: groq llama-3.1-8b-instant`

Health check setelah app jalan:
```bash
curl http://localhost:5000/health
```
