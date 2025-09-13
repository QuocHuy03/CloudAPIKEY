from flask import Blueprint, request, jsonify
from services.key_service_wrapper import check_key_validity
from database import db_manager


merger_video_ai_bp = Blueprint('merger_video_ai', __name__)

@merger_video_ai_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        # Log failed authentication attempt
        db_manager.log_api_usage(
            key_value=key or "unknown",
            module="merger_video_ai",
            device_id=device_id or "unknown",
            endpoint="/auth",
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            request_data=f"key={key}&device_id={device_id}",
            response_status=400,
            response_message="Missing key or device_id"
        )
        return jsonify(success=False, message="🔒 Thiếu trường key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="merger_video_ai")
    if not is_valid:
        # Log failed authentication
        db_manager.log_api_usage(
            key_value=key,
            module="merger_video_ai",
            device_id=device_id,
            endpoint="/auth",
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            request_data=f"key={key}&device_id={device_id}",
            response_status=403,
            response_message=msg
        )
        return jsonify(success=False, message=msg), 403

    # Log successful authentication
    db_manager.log_api_usage(
        key_value=key,
        module="merger_video_ai",
        device_id=device_id,
        endpoint="/auth",
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        request_data=f"key={key}&device_id={device_id}",
        response_status=200,
        response_message="Authentication successful"
    )

    return jsonify(
        success=True,
        message="✅ Xác thực thành công",
        expires=expires if expires else "",
        remaining=remaining
    ), 200

