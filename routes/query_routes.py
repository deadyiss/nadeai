from flask import Blueprint, request, jsonify

from core.query_processor import get_query_processor
from routes import require_auth
from utils.response_builder import success_response, error_response

query_bp = Blueprint("query", __name__, url_prefix="/api")


@query_bp.route("/query", methods=["POST"])
@require_auth
def query(current_user):
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    if not q:
        body, status = error_response("Query text required", status_code=400)
        return jsonify(body), status

    top_k = data.get("top_k")
    if top_k is not None:
        try:
            top_k = int(top_k)
            if top_k < 1 or top_k > 20:
                raise ValueError()
        except (ValueError, TypeError):
            body, status = error_response("top_k must be int 1-20", status_code=400)
            return jsonify(body), status

    try:
        processor = get_query_processor()
        result = processor.process(
            query=q,
            user_id=current_user["id"],
            include_shared=True,
            top_k=top_k,
            save_history=True,
        )
        return jsonify(success_response(data=result))
    except ValueError as e:
        body, status = error_response(str(e), status_code=400)
        return jsonify(body), status
    except Exception as e:
        body, status = error_response(f"Query failed: {e}", status_code=500)
        return jsonify(body), status