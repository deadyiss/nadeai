from flask import Blueprint, request, jsonify

from core.auth_manager import get_auth_manager, AuthError
from routes import require_auth, _extract_token
from utils.response_builder import success_response, error_response

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        user = get_auth_manager().register(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email"),
            role="user",  # public registration always = user
        )
        return jsonify(success_response(data={"user": user}, message="Registration successful"))
    except AuthError as e:
        body, status = error_response(str(e), code="REGISTRATION_FAILED", status_code=400)
        return jsonify(body), status


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    try:
        result = get_auth_manager().login(
            username=data.get("username", ""),
            password=data.get("password", ""),
        )
        return jsonify(success_response(data=result, message="Login successful"))
    except AuthError as e:
        body, status = error_response(str(e), code="LOGIN_FAILED", status_code=401)
        return jsonify(body), status


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout(current_user):
    token = _extract_token()
    ok = get_auth_manager().logout(token)
    if ok:
        return jsonify(success_response(message="Logout successful"))
    body, status = error_response("Logout failed", status_code=400)
    return jsonify(body), status


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me(current_user):
    return jsonify(success_response(data={"user": current_user}))