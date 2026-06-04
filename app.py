"""
<<<<<<< HEAD
Local RAG System — Flask application entry point.
Run: python3 app.py
LAN access: http://<server-ip>:5000
"""
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
from waitress import serve

import config
from models import init_db
from core.auth_manager import get_auth_manager
=======
Nade AI — Flask application entry point.
UI: NadeAI design (session-based, server-rendered)
Backend: PrivaQuery full feature set (RAG + OCR + hallucination + conflict detection)
"""
import json
import os
import sys
import uuid
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory,
)
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from waitress import serve
from werkzeug.utils import secure_filename

import config
from models import init_db
from core.auth_manager import get_auth_manager, AuthError
from core.document_processor import get_document_processor
from core.ocr_engine import get_ocr_engine
from core.vector_store import get_vector_store
from core.query_processor import get_query_processor
from models import get_session, Document, User, QueryHistory, ConflictLog
from routes.health_routes import health_bp
>>>>>>> 0c7befc (Final Revision)
from routes.auth_routes import auth_bp
from routes.document_routes import doc_bp
from routes.query_routes import query_bp
from routes.admin_routes import admin_bp
<<<<<<< HEAD
from routes.health_routes import health_bp
from utils.logger import get_logger
from utils.response_builder import error_response
=======
from utils.file_validator import sanitize_filename, FileValidationError
from utils.logger import get_logger
from utils.text_cleaner import chunk_text
>>>>>>> 0c7befc (Final Revision)

logger = get_logger("app")


<<<<<<< HEAD
=======
# ─────────────────────────────────────────
# Helper: current user from Flask session
# ─────────────────────────────────────────

class CurrentUser:
    """Thin wrapper to expose user dict as object attributes in templates."""
    def __init__(self, data: dict):
        self._data = data
        self.id = data.get("id")
        self.username = data.get("username", "")
        self.email = data.get("email", "")
        self.role = data.get("role", "user")
        self.is_active = data.get("is_active", True)

    @property
    def is_admin(self):
        return self.role == "admin"

    def __getitem__(self, item):
        return self._data[item]

    def get(self, key, default=None):
        return self._data.get(key, default)


def get_current_user():
    token = session.get("token")
    if not token:
        return None
    user_dict = get_auth_manager().verify_token(token)
    if not user_dict:
        session.clear()
        return None
    return CurrentUser(user_dict)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("login"))
        return f(*args, current_user=user, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            flash("Silakan login terlebih dahulu.", "error")
            return redirect(url_for("login"))
        if not user.is_admin:
            flash("Akses ditolak. Halaman ini hanya untuk admin.", "error")
            return redirect(url_for("index"))
        return f(*args, current_user=user, **kwargs)
    return wrapper


# ─────────────────────────────────────────
# App factory
# ─────────────────────────────────────────

>>>>>>> 0c7befc (Final Revision)
def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE_BYTES
<<<<<<< HEAD

    # CORS — allow LAN clients
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints
=======
    app.config["WTF_CSRF_ENABLED"] = True
    # Don't let browsers cache CSS/JS during development (avoids stale-asset bugs)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    csrf = CSRFProtect(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register JSON API blueprints (for API clients)
>>>>>>> 0c7befc (Final Revision)
    app.register_blueprint(auth_bp)
    app.register_blueprint(doc_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)

<<<<<<< HEAD
    # ----- HTML routes -----
    @app.route("/")
    def index():
        if Path(app.template_folder, "index.html").exists():
            return render_template("index.html")
        return jsonify({"name": "Local RAG System", "status": "running",
                        "ui": "templates/index.html not yet created"})

    @app.route("/login")
    def login_page():
        if Path(app.template_folder, "login.html").exists():
            return render_template("login.html")
        return jsonify({"message": "login.html not yet created"})

    @app.route("/register")
    def register_page():
        if Path(app.template_folder, "register.html").exists():
            return render_template("register.html")
        return jsonify({"message": "register.html not yet created"})

    @app.route("/admin")
    def admin_page():
        admin_index = Path(app.template_folder, "admin", "dashboard.html")
        if admin_index.exists():
            return render_template("admin/dashboard.html")
        return jsonify({"message": "admin/dashboard.html not yet created"})

    @app.route("/admin/users-page")
    def admin_users_page():
        p = Path(app.template_folder, "admin", "users.html")
        if p.exists():
            return render_template("admin/users.html")
        return jsonify({"message": "admin/users.html not yet created"})

    @app.route("/admin/documents-page")
    def admin_documents_page():
        p = Path(app.template_folder, "admin", "documents.html")
        if p.exists():
            return render_template("admin/documents.html")
        return jsonify({"message": "admin/documents.html not yet created"})

    # ----- Error handlers -----
    @app.errorhandler(404)
    def not_found(e):
        body, status = error_response("Not found", code="NOT_FOUND", status_code=404)
        return jsonify(body), status

    @app.errorhandler(413)
    def too_large(e):
        body, status = error_response(
            f"File exceeds {config.MAX_FILE_SIZE_MB} MB limit",
            code="FILE_TOO_LARGE", status_code=413,
        )
        return jsonify(body), status

    @app.errorhandler(405)
    def method_not_allowed(e):
        body, status = error_response("Method not allowed",
                                       code="METHOD_NOT_ALLOWED", status_code=405)
        return jsonify(body), status
=======
    # ── Template context ─────────────────────────
    @app.context_processor
    def inject_globals():
        return {
            "max_file_size_mb": config.MAX_FILE_SIZE_MB,
        }

    # ── HTML Routes ──────────────────────────────

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if get_current_user():
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            try:
                result = get_auth_manager().login(username, password)
                session["token"] = result["token"]
                session["user_id"] = result["user"]["id"]
                return redirect(url_for("index"))
            except AuthError as e:
                flash(str(e), "error")
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if get_current_user():
            return redirect(url_for("index"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip() or None
            password = request.form.get("password", "")
            try:
                get_auth_manager().register(username=username, password=password, email=email)
                flash("Akun berhasil dibuat. Silakan login.", "success")
                return redirect(url_for("login"))
            except AuthError as e:
                flash(str(e), "error")
        return render_template("register.html")

    @app.route("/logout")
    def logout():
        token = session.get("token")
        if token:
            get_auth_manager().logout(token)
        session.clear()
        return redirect(url_for("login"))

    @app.route("/", methods=["GET", "POST"])
    @login_required
    def index(current_user):
        answer = None
        question = None
        sources = []
        confidence = None
        has_conflict = False
        conflict_details = []
        hallucination = None
        execution_time_ms = None

        if request.method == "POST":
            question = (request.form.get("question") or "").strip()
            if question:
                try:
                    processor = get_query_processor()
                    result = processor.process(
                        query=question,
                        user_id=current_user.id,
                        include_shared=True,
                        save_history=True,
                    )
                    answer = result["answer"]
                    sources = [s["filename"] for s in result.get("sources", [])]
                    confidence = result.get("confidence", 0)
                    has_conflict = result.get("has_conflict", False)
                    conflict_details = result.get("conflict_details", [])
                    hallucination = result.get("hallucination", {})
                    execution_time_ms = result.get("execution_time_ms")
                except Exception as e:
                    logger.exception("Query failed")
                    flash(f"Query gagal: {e}", "error")

        # Documents list
        with get_session() as s:
            if current_user.is_admin:
                docs = (s.query(Document)
                        .filter(Document.chunk_index == 0)
                        .order_by(Document.created_at.desc()).all())
            else:
                docs = (
                    s.query(Document)
                    .filter(
                        Document.chunk_index == 0,
                        (Document.user_id == current_user.id) | (Document.is_shared == True)
                    )
                    .order_by(Document.created_at.desc())
                    .all()
                )

        return render_template(
            "index.html",
            current_user=current_user,
            documents=docs,
            question=question,
            answer=answer,
            sources=sources,
            confidence=confidence,
            has_conflict=has_conflict,
            conflict_details=conflict_details,
            hallucination=hallucination,
            execution_time_ms=execution_time_ms,
        )

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload(current_user):
        if "file" not in request.files:
            flash("Tidak ada file yang diupload.", "error")
            return redirect(url_for("index"))

        f = request.files["file"]
        if not f or not f.filename:
            flash("Nama file kosong.", "error")
            return redirect(url_for("index"))

        is_shared_raw = request.form.get("shared", "0")
        is_shared = is_shared_raw in ("1", "true", "True")
        if is_shared and not current_user.is_admin:
            flash("Hanya admin yang dapat mengupload dokumen shared.", "error")
            return redirect(url_for("index"))

        safe_original = sanitize_filename(secure_filename(f.filename))
        storage_name = f"{uuid.uuid4().hex}_{safe_original}"

        user_dir = Path(config.UPLOAD_FOLDER) / str(current_user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        final_path = user_dir / storage_name
        temp_path = Path(config.TEMP_UPLOAD_FOLDER) / storage_name
        temp_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            f.save(str(temp_path))
        except Exception as e:
            flash(f"Gagal menyimpan file: {e}", "error")
            return redirect(url_for("index"))

        try:
            processor = get_document_processor()
            result = processor.process(str(temp_path), original_filename=safe_original)
        except FileValidationError as e:
            temp_path.unlink(missing_ok=True)
            flash(str(e), "error")
            return redirect(url_for("index"))
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            logger.exception("Document processing failed")
            flash(f"Pemrosesan gagal: {e}", "error")
            return redirect(url_for("index"))

        try:
            temp_path.replace(final_path)
        except Exception as e:
            temp_path.unlink(missing_ok=True)
            flash(f"Gagal menyimpan file permanen: {e}", "error")
            return redirect(url_for("index"))

        chunks = chunk_text(result["text"], chunk_size=300, overlap=50)
        if not chunks:
            chunks = [result["text"]]
        chunk_total = len(chunks)

        try:
            store = get_vector_store()
            with get_session() as s:
                for idx, chunk in enumerate(chunks):
                    doc = Document(
                        user_id=current_user.id,
                        filename=safe_original,
                        filepath=str(final_path),
                        text=chunk,
                        word_count=len(chunk.split()),
                        dates=json.dumps(result["dates"]) if idx == 0 else json.dumps([]),
                        is_shared=is_shared,
                        chunk_index=idx,
                        chunk_total=chunk_total,
                    )
                    s.add(doc)
                    s.commit()
                    s.refresh(doc)
                    store.add(doc, s)
                    s.commit()

            flash(
                f"Dokumen '{safe_original}' berhasil diupload dan diindex "
                f"({chunk_total} chunk{'s' if chunk_total > 1 else ''}).",
                "success"
            )
        except Exception as e:
            final_path.unlink(missing_ok=True)
            logger.exception("DB insert failed")
            flash(f"Indexing gagal: {e}", "error")

        return redirect(url_for("index"))

    @app.route("/scan", methods=["POST"])
    @csrf.exempt
    @login_required
    def scan(current_user):
        """Multi-page camera scan: OCR several photos, combine into ONE document.

        Expects multipart form with:
          - pages   : one or more image files (in page order)
          - doc_name: document name set by the user
          - shared  : "1" for shared (admin only)
        Returns JSON so the client can flag pages that failed OCR (for retake).
        """
        files = request.files.getlist("pages")
        files = [f for f in files if f and f.filename]
        if not files:
            return jsonify({"ok": False, "error": "Tidak ada halaman yang discan."}), 400

        raw_name = (request.form.get("doc_name") or "").strip()
        if not raw_name:
            return jsonify({"ok": False, "error": "Nama dokumen wajib diisi."}), 400

        is_shared = request.form.get("shared", "0") in ("1", "true", "True", "on")
        if is_shared and not current_user.is_admin:
            return jsonify({"ok": False, "error": "Hanya admin yang dapat membuat dokumen shared."}), 403

        max_pages = getattr(config, "MAX_SCAN_PAGES", 20)
        if len(files) > max_pages:
            return jsonify({"ok": False, "error": f"Maksimal {max_pages} halaman per dokumen."}), 400

        ocr = get_ocr_engine()
        page_texts, failed_pages, per_page = [], [], []
        tmp_dir = Path(config.TEMP_UPLOAD_FOLDER)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        for idx, f in enumerate(files, start=1):
            tmp = tmp_dir / f"scan_{uuid.uuid4().hex}"
            try:
                f.save(str(tmp))
                res = ocr.extract(str(tmp))
                text = (res.get("text") or "").strip()
                conf = res.get("confidence", 0.0)
                if text:
                    page_texts.append(text)
                    per_page.append({"index": idx, "ok": True, "confidence": round(conf, 2)})
                else:
                    failed_pages.append(idx)
                    per_page.append({"index": idx, "ok": False, "confidence": round(conf, 2)})
            except Exception as e:
                logger.warning(f"Scan page {idx} failed: {e}")
                failed_pages.append(idx)
                per_page.append({"index": idx, "ok": False, "confidence": 0.0})
            finally:
                tmp.unlink(missing_ok=True)

        if not page_texts:
            return jsonify({
                "ok": False,
                "error": "Tidak ada teks yang bisa dibaca dari halaman manapun. Foto ulang dengan pencahayaan lebih baik.",
                "failed_pages": failed_pages,
                "per_page": per_page,
            }), 400

        combined = "\n\n".join(page_texts)

        # Persist combined text as a .txt file, then reuse the normal pipeline.
        safe_name = sanitize_filename(secure_filename(raw_name))
        if not safe_name.lower().endswith(".txt"):
            safe_name += ".txt"
        storage_name = f"{uuid.uuid4().hex}_{safe_name}"
        user_dir = Path(config.UPLOAD_FOLDER) / str(current_user.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        final_path = user_dir / storage_name

        try:
            final_path.write_text(combined, encoding="utf-8")
            result = get_document_processor().process(str(final_path), original_filename=safe_name)
        except Exception as e:
            final_path.unlink(missing_ok=True)
            logger.exception("Scan processing failed")
            return jsonify({"ok": False, "error": f"Pemrosesan gagal: {e}"}), 500

        chunks = chunk_text(result["text"], chunk_size=300, overlap=50) or [result["text"]]
        chunk_total = len(chunks)

        try:
            store = get_vector_store()
            with get_session() as s:
                for idx, chunk in enumerate(chunks):
                    doc = Document(
                        user_id=current_user.id,
                        filename=safe_name,
                        filepath=str(final_path),
                        text=chunk,
                        word_count=len(chunk.split()),
                        dates=json.dumps(result["dates"]) if idx == 0 else json.dumps([]),
                        is_shared=is_shared,
                        chunk_index=idx,
                        chunk_total=chunk_total,
                    )
                    s.add(doc)
                    s.commit()
                    s.refresh(doc)
                    store.add(doc, s)
                    s.commit()
        except Exception as e:
            final_path.unlink(missing_ok=True)
            logger.exception("Scan indexing failed")
            return jsonify({"ok": False, "error": f"Indexing gagal: {e}"}), 500

        return jsonify({
            "ok": True,
            "filename": safe_name,
            "pages_total": len(files),
            "pages_ok": len(page_texts),
            "failed_pages": failed_pages,
            "per_page": per_page,
            "word_count": result["word_count"],
            "chunks": chunk_total,
        })

    @app.route("/document/<int:doc_id>/delete", methods=["POST"])
    @login_required
    def delete_document(current_user, doc_id):
        with get_session() as s:
            doc = s.query(Document).filter(Document.id == doc_id).one_or_none()
            if doc is None:
                flash("Dokumen tidak ditemukan.", "error")
                return redirect(url_for("index"))

            is_owner = doc.user_id == current_user.id
            if not (is_owner or current_user.is_admin):
                flash("Tidak diizinkan.", "error")
                return redirect(url_for("index"))

            filepath = doc.filepath
            store = get_vector_store()
            all_chunks = s.query(Document).filter(Document.filepath == filepath).all()
            for chunk_doc in all_chunks:
                store.remove(chunk_doc.id, s)
                s.delete(chunk_doc)
            s.commit()

            try:
                Path(filepath).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to remove file {filepath}: {e}")

        flash("Dokumen berhasil dihapus.", "success")
        return redirect(url_for("index"))

    # ── Admin HTML Routes ─────────────────────────

    @app.route("/admin")
    @app.route("/admin/dashboard")
    @admin_required
    def admin_dashboard(current_user):
        with get_session() as s:
            stats = {
                "total_users": s.query(User).count(),
                "active_users": s.query(User).filter(User.is_active == True).count(),
                "admin_count": s.query(User).filter(User.role == "admin").count(),
                "total_documents": s.query(Document).filter(Document.chunk_index == 0).count(),
                "shared_documents": s.query(Document).filter(
                    Document.is_shared == True, Document.chunk_index == 0
                ).count(),
                "total_queries": s.query(QueryHistory).count(),
                "conflict_queries": s.query(QueryHistory).filter(
                    QueryHistory.has_conflict == True
                ).count(),
                "total_conflicts": s.query(ConflictLog).count(),
            }

            # Query history with username join
            rows_raw = (
                s.query(QueryHistory, User.username)
                .join(User, QueryHistory.user_id == User.id)
                .order_by(QueryHistory.created_at.desc())
                .limit(50)
                .all()
            )
            query_history = []
            for qh, uname in rows_raw:
                query_history.append({
                    "created_at": qh.created_at,
                    "username": uname,
                    "query": qh.query_text,
                    "confidence": qh.confidence or 0,
                    "has_conflict": qh.has_conflict,
                    "exec_ms": int(qh.execution_time or 0),
                })

        vector_store = get_vector_store().stats()

        return render_template(
            "admin/dashboard.html",
            current_user=current_user,
            stats=stats,
            vector_store=vector_store,
            query_history=query_history,
        )

    @app.route("/admin/users")
    @admin_required
    def admin_users(current_user):
        with get_session() as s:
            users = s.query(User).order_by(User.created_at.desc()).all()
            users_list = [u.to_dict() for u in users]
        return render_template(
            "admin/users.html",
            current_user=current_user,
            users=users_list,
        )

    @app.route("/admin/users/create", methods=["POST"])
    @admin_required
    def admin_create_user(current_user):
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip() or None
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        try:
            get_auth_manager().register(
                username=username, password=password, email=email, role=role
            )
            flash(f"User '{username}' berhasil dibuat.", "success")
        except AuthError as e:
            flash(str(e), "error")
        return redirect(url_for("admin_users"))

    @app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_user(current_user, user_id):
        if user_id == current_user.id:
            flash("Tidak bisa menghapus akun sendiri.", "error")
            return redirect(url_for("admin_users"))

        with get_session() as s:
            user = s.query(User).filter(User.id == user_id).one_or_none()
            if user is None:
                flash("User tidak ditemukan.", "error")
                return redirect(url_for("admin_users"))

            store = get_vector_store()
            docs = s.query(Document).filter(Document.user_id == user_id).all()
            for d in docs:
                store.remove(d.id, s)
            s.delete(user)
            s.commit()

        flash("User berhasil dihapus.", "success")
        return redirect(url_for("admin_users"))

    @app.route("/admin/documents")
    @admin_required
    def admin_documents(current_user):
        with get_session() as s:
            rows = (
                s.query(Document, User.username)
                .join(User, Document.user_id == User.id)
                .filter(Document.chunk_index == 0)
                .order_by(Document.created_at.desc())
                .all()
            )
            documents = []
            for doc, uname in rows:
                d = doc.to_dict()
                d["owner"] = uname
                d["created_at"] = doc.created_at
                documents.append(d)

        return render_template(
            "admin/documents.html",
            current_user=current_user,
            documents=documents,
        )

    @app.route("/admin/documents/<int:doc_id>/delete", methods=["POST"])
    @admin_required
    def admin_delete_document(current_user, doc_id):
        with get_session() as s:
            doc = s.query(Document).filter(Document.id == doc_id).one_or_none()
            if doc is None:
                flash("Dokumen tidak ditemukan.", "error")
                return redirect(url_for("admin_documents"))

            filepath = doc.filepath
            store = get_vector_store()
            all_chunks = s.query(Document).filter(Document.filepath == filepath).all()
            for chunk_doc in all_chunks:
                store.remove(chunk_doc.id, s)
                s.delete(chunk_doc)
            s.commit()
            try:
                Path(filepath).unlink(missing_ok=True)
            except Exception:
                pass

        flash("Dokumen berhasil dihapus.", "success")
        return redirect(url_for("admin_documents"))

    # ── Error handlers ─────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        flash(f"File terlalu besar. Maksimum {config.MAX_FILE_SIZE_MB} MB.", "error")
        return redirect(url_for("index"))
>>>>>>> 0c7befc (Final Revision)

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
<<<<<<< HEAD
        body, status = error_response("Internal server error",
                                       code="INTERNAL_ERROR", status_code=500)
        return jsonify(body), status
=======
        return render_template("errors/500.html"), 500
>>>>>>> 0c7befc (Final Revision)

    return app


def bootstrap():
<<<<<<< HEAD
    """Initialize DB and ensure admin user exists."""
    logger.info("=" * 60)
    logger.info("Local RAG System — bootstrapping")
=======
    logger.info("=" * 60)
    logger.info("Nade AI — bootstrapping")
>>>>>>> 0c7befc (Final Revision)
    logger.info("=" * 60)

    init_db()

    admin = get_auth_manager().ensure_admin()
    if admin:
        logger.warning(
<<<<<<< HEAD
            f"Default admin available: username={config.ADMIN_USERNAME} "
            f"(set ADMIN_PASSWORD in .env for production)"
        )

    # Eager-load heavy components so first user query isn't slow
=======
            f"Default admin: username={config.ADMIN_USERNAME} "
            f"(atur ADMIN_PASSWORD di .env untuk produksi)"
        )

>>>>>>> 0c7befc (Final Revision)
    logger.info("Pre-loading embedding model...")
    from core.embedding_engine import get_embedding_engine
    get_embedding_engine()

    logger.info("Pre-loading vector store...")
<<<<<<< HEAD
    from core.vector_store import get_vector_store
=======
>>>>>>> 0c7befc (Final Revision)
    get_vector_store()

    logger.info("Pre-loading LLM engine...")
    from core.llm_engine import get_llm_engine
    llm = get_llm_engine()
    if not llm.health_check():
        logger.warning(
<<<<<<< HEAD
            f"LLM ({config.LLM_MODEL}) not reachable at {config.OLLAMA_HOST}. "
            f"Start Ollama or check OLLAMA_HOST in .env"
        )

    logger.info("Pre-loading NLI model for hallucination check...")
    from core.hallucination_checker import get_hallucination_checker
    get_hallucination_checker()

    logger.info("Bootstrap complete.")
=======
            f"LLM ({config.LLM_MODEL}) tidak dapat dijangkau di {config.OLLAMA_HOST}. "
            f"Jalankan Ollama atau cek OLLAMA_HOST di .env"
        )

    logger.info("Pre-loading NLI model untuk hallucination check...")
    from core.hallucination_checker import get_hallucination_checker
    get_hallucination_checker()

    logger.info("Bootstrap selesai.")
>>>>>>> 0c7befc (Final Revision)


def main():
    bootstrap()
    app = create_app()

    host = config.FLASK_HOST
    port = config.FLASK_PORT
    env = config.FLASK_ENV

<<<<<<< HEAD
    logger.info(f"Starting server: http://{host}:{port} (env={env})")
    logger.info(f"LAN access: http://<this-machine-ip>:{port}")
=======
    logger.info(f"Server berjalan: http://{host}:{port} (env={env})")
    logger.info(f"LAN access: http://<ip-mesin>:{port}")
>>>>>>> 0c7befc (Final Revision)

    if env == "development":
        app.run(host=host, port=port, debug=False, use_reloader=False)
    else:
<<<<<<< HEAD
        # Production: waitress (Python 3.14 compatible, gunicorn tidak support)
=======
>>>>>>> 0c7befc (Final Revision)
        serve(app, host=host, port=port, threads=8)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
<<<<<<< HEAD
        logger.info("Shutting down (KeyboardInterrupt)")
=======
        logger.info("Shutdown (KeyboardInterrupt)")
>>>>>>> 0c7befc (Final Revision)
        sys.exit(0)
