import os
from dotenv import load_dotenv

load_dotenv()

# ----------------------------
# BASE
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------
# FLASK
# ----------------------------
FLASK_ENV        = os.getenv("FLASK_ENV", "development")
FLASK_HOST       = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT       = int(os.getenv("FLASK_PORT", 5000))
SECRET_KEY       = os.getenv("SECRET_KEY", "3f7a9c2e1b4d6f8a0e5c7b9d2f4a6e8c1b3d5f7a9c2e4b6d8f0a2c4e6b8d0f2")

# ----------------------------
# DATABASE
# ----------------------------
DATABASE_URL     = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE_DIR, "data", "app.db").replace("\\", "/")
)

# ----------------------------
# FILE STORAGE
# ----------------------------
UPLOAD_FOLDER       = os.path.join(BASE_DIR, "data", "documents")
TEMP_UPLOAD_FOLDER  = os.path.join(BASE_DIR, "data", "uploads")
MAX_FILE_SIZE_MB    = int(os.getenv("MAX_FILE_SIZE_MB", 100))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_SCAN_PAGES      = int(os.getenv("MAX_SCAN_PAGES", 20))
ALLOWED_EXTENSIONS  = {"pdf", "docx", "txt", "jpg", "jpeg", "png", "bmp", "tiff"}

# ----------------------------
# AI MODELS
# ----------------------------
EMBEDDING_MODEL  = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
EMBEDDING_DIM    = 384
LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL        = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY", "")
OLLAMA_HOST      = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# ----------------------------
# OCR
# ----------------------------
OCR_LANGUAGES        = ["en", "id"]
TESSERACT_CONFIG     = "--oem 3 --psm 6 -l eng+ind"
RAPIDOCR_LANGUAGES   = ["en", "id"]

# ----------------------------
# ALGORITHM
# ----------------------------
HALLUCINATION_THRESHOLD  = float(os.getenv("HALLUCINATION_THRESHOLD", 0.6))
TOP_K_DOCUMENTS          = int(os.getenv("TOP_K_DOCUMENTS", 5))
SIMILARITY_MIN_THRESHOLD = float(os.getenv("SIMILARITY_MIN_THRESHOLD", 0.15))

# ----------------------------
# NLI
# ----------------------------
NLI_ENTAILMENT_THRESHOLD    = float(os.getenv("NLI_ENTAILMENT_THRESHOLD", 0.5))
NLI_CONTRADICTION_THRESHOLD = float(os.getenv("NLI_CONTRADICTION_THRESHOLD", 0.5))

# ----------------------------
# SESSION
# ----------------------------
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", 24))

# ----------------------------
# LOGGING
# ----------------------------
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO")

# ----------------------------
# ADMIN BOOTSTRAP
# ----------------------------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_EMAIL    = os.getenv("ADMIN_EMAIL", "admin@local")