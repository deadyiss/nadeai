from functools import wraps
from flask import request, jsonify

from core.auth_manager import get_auth_manager
from utils.response_builder import error_response


def _extract_token() -> str:
    """Extract bearer token from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def require_auth(f):
    """Decorator: require valid token. Injects `current_user` (dict) into kwargs."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        user = get_auth_manager().verify_token(token)
        if user is None:
            body, status = error_response("Unauthorized", code="AUTH_REQUIRED", status_code=401)
            return jsonify(body), status
        kwargs["current_user"] = user
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    """Decorator: require valid token + admin role."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        user = get_auth_manager().verify_token(token)
        if user is None:
            body, status = error_response("Unauthorized", code="AUTH_REQUIRED", status_code=401)
            return jsonify(body), status
        if user.get("role") != "admin":
            body, status = error_response("Admin only", code="FORBIDDEN", status_code=403)
            return jsonify(body), status
        kwargs["current_user"] = user
        return f(*args, **kwargs)
    return wrapper