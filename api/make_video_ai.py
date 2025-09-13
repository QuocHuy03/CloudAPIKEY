from flask import Blueprint, request, jsonify
from services.key_service_wrapper import check_key_validity
from services.key_service import check_key_validity


make_video_ai_bp = Blueprint('make_video_ai', __name__)

@make_video_ai_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        return jsonify(success=False, message="🔒 Thiếu trường key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="make_video_ai")
    if not is_valid:
        return jsonify(success=False, message=msg), 403

    return jsonify(
        success=True,
        message="✅ Xác thực thành công",
        expires=expires.strftime("%Y-%m-%d") if expires else "",
        remaining=remaining
    ), 200

