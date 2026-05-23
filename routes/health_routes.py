from flask import Blueprint, jsonify

from core.llm_engine import get_llm_engine
from core.vector_store import get_vector_store
from models import get_session, User
from utils.response_builder import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    checks = {}

    # DB
    try:
        with get_session() as s:
            s.query(User).count()
            checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # LLM
    try:
        checks["llm"] = "ok" if get_llm_engine().health_check() else "error: not reachable"
    except Exception as e:
        checks["llm"] = f"error: {e}"

    # Vector store
    try:
        stats = get_vector_store().stats()
        checks["vector_store"] = f"ok ({stats['total_vectors']} vectors)"
    except Exception as e:
        checks["vector_store"] = f"error: {e}"

    overall_ok = all(v.startswith("ok") for v in checks.values())

    return jsonify(success_response(
        data={"status": "healthy" if overall_ok else "degraded", "checks": checks}
    )), (200 if overall_ok else 503)