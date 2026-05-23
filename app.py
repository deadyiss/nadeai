"""
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
from routes.auth_routes import auth_bp
from routes.document_routes import doc_bp
from routes.query_routes import query_bp
from routes.admin_routes import admin_bp
from routes.health_routes import health_bp
from utils.logger import get_logger
from utils.response_builder import error_response

logger = get_logger("app")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_FILE_SIZE_BYTES

    # CORS — allow LAN clients
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(doc_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)

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

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Internal server error")
        body, status = error_response("Internal server error",
                                       code="INTERNAL_ERROR", status_code=500)
        return jsonify(body), status

    return app


def bootstrap():
    """Initialize DB and ensure admin user exists."""
    logger.info("=" * 60)
    logger.info("Local RAG System — bootstrapping")
    logger.info("=" * 60)

    init_db()

    admin = get_auth_manager().ensure_admin()
    if admin:
        logger.warning(
            f"Default admin available: username={config.ADMIN_USERNAME} "
            f"(set ADMIN_PASSWORD in .env for production)"
        )

    # Eager-load heavy components so first user query isn't slow
    logger.info("Pre-loading embedding model...")
    from core.embedding_engine import get_embedding_engine
    get_embedding_engine()

    logger.info("Pre-loading vector store...")
    from core.vector_store import get_vector_store
    get_vector_store()

    logger.info("Pre-loading LLM engine...")
    from core.llm_engine import get_llm_engine
    llm = get_llm_engine()
    if not llm.health_check():
        logger.warning(
            f"LLM ({config.LLM_MODEL}) not reachable at {config.OLLAMA_HOST}. "
            f"Start Ollama or check OLLAMA_HOST in .env"
        )

    logger.info("Pre-loading NLI model for hallucination check...")
    from core.hallucination_checker import get_hallucination_checker
    get_hallucination_checker()

    logger.info("Bootstrap complete.")


def main():
    bootstrap()
    app = create_app()

    host = config.FLASK_HOST
    port = config.FLASK_PORT
    env = config.FLASK_ENV

    logger.info(f"Starting server: http://{host}:{port} (env={env})")
    logger.info(f"LAN access: http://<this-machine-ip>:{port}")

    if env == "development":
        app.run(host=host, port=port, debug=False, use_reloader=False)
    else:
        # Production: waitress (Python 3.14 compatible, gunicorn tidak support)
        serve(app, host=host, port=port, threads=8)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt)")
        sys.exit(0)
