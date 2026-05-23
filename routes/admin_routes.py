import json

from flask import Blueprint, request, jsonify

from core.auth_manager import get_auth_manager, AuthError
from core.vector_store import get_vector_store
from models import get_session, User, Document, QueryHistory, ConflictLog
from routes import require_admin
from utils.response_builder import success_response, error_response

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@require_admin
def dashboard(current_user):
    with get_session() as s:
        stats = {
            "total_users": s.query(User).count(),
            "active_users": s.query(User).filter(User.is_active == True).count(),
            "admin_users": s.query(User).filter(User.role == "admin").count(),
            "total_documents": s.query(Document).count(),
            "shared_documents": s.query(Document).filter(Document.is_shared == True).count(),
            "total_queries": s.query(QueryHistory).count(),
            "queries_with_conflict": s.query(QueryHistory).filter(QueryHistory.has_conflict == True).count(),
            "total_conflicts_logged": s.query(ConflictLog).count(),
        }
        vector_stats = get_vector_store().stats()
        return jsonify(success_response(data={
            "stats": stats,
            "vector_store": vector_stats,
        }))


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users(current_user):
    with get_session() as s:
        users = s.query(User).order_by(User.created_at.desc()).all()
        return jsonify(success_response(data={
            "users": [u.to_dict() for u in users],
            "count": len(users),
        }))


@admin_bp.route("/users", methods=["POST"])
@require_admin
def create_user(current_user):
    data = request.get_json(silent=True) or {}
    role = data.get("role", "user")
    if role not in ("admin", "user"):
        body, status = error_response(f"Invalid role: {role}", status_code=400)
        return jsonify(body), status
    try:
        user = get_auth_manager().register(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email"),
            role=role,
        )
        return jsonify(success_response(data={"user": user}, message="User created"))
    except AuthError as e:
        body, status = error_response(str(e), status_code=400)
        return jsonify(body), status


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_admin
def delete_user(current_user, user_id):
    if user_id == current_user["id"]:
        body, status = error_response("Cannot delete self", status_code=400)
        return jsonify(body), status

    with get_session() as s:
        user = s.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            body, status = error_response("User not found", status_code=404)
            return jsonify(body), status
        # Cascade: documents + their embeddings + sessions + queries (cascade configured in models)
        # Remove vectors from in-memory store first
        store = get_vector_store()
        docs = s.query(Document).filter(Document.user_id == user_id).all()
        for d in docs:
            store.remove(d.id, s)
        s.delete(user)
        s.commit()
        return jsonify(success_response(message=f"User {user_id} deleted"))


@admin_bp.route("/documents", methods=["GET"])
@require_admin
def all_documents(current_user):
    with get_session() as s:
        docs = s.query(Document).order_by(Document.created_at.desc()).all()
        return jsonify(success_response(data={
            "documents": [d.to_dict() for d in docs],
            "count": len(docs),
        }))


@admin_bp.route("/queries", methods=["GET"])
@require_admin
def all_queries(current_user):
    limit = request.args.get("limit", 100, type=int)
    limit = max(1, min(limit, 500))
    with get_session() as s:
        rows = (
            s.query(QueryHistory)
            .order_by(QueryHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return jsonify(success_response(data={
            "queries": [r.to_dict() for r in rows],
            "count": len(rows),
        }))