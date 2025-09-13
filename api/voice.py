from flask import Blueprint, request, jsonify, send_from_directory
from services.voice_service import (
    create_voice, use_voice_key, get_voice_list, get_key_status_key
)
from services.key_service_wrapper import check_key_validity
from middlewares.auth import require_auth
from database import db_manager

voice_bp = Blueprint('voice', __name__)

@voice_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        return jsonify(success=False, message="🔒 Thiếu key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="voice")
    if not is_valid:
        # Log failed authentication
        db_manager.log_api_usage(
            key_value=key,
            module="voice",
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
        module="voice",
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
        expires=expires.strftime("%Y-%m-%d") if expires else "",
        remaining=remaining
    ), 200


@voice_bp.route("/play/<path:filename>")
def serve_voice_sample(filename):
    return send_from_directory("voices", filename)


@voice_bp.route("/list", methods=["GET"])
def list_voices_api():
    base_url = request.host_url.rstrip("/")
    voices = get_voice_list(base_url=base_url)
    return jsonify({"success": True, "voices": voices})


@voice_bp.route("/create", methods=["POST"])
@require_auth(module="voice")
def create_voice_api():
    data = request.form
    text = data.get("text", "").strip()
    voice_code = data.get("voice_code", "achird").strip()
    key = data.get("key", "").strip()
    device_id = data.get("device_id", "").strip()

    if not text:
        return jsonify(success=False, message="❌ Thiếu text"), 400
    if not key or not device_id:
        return jsonify(success=False, message="❌ Thiếu key hoặc device_id"), 400

    success, message, file_name, duration  = create_voice(text, key, device_id, voice_code)
    if not success:
        # Log failed voice creation
        db_manager.log_api_usage(
            key_value=key,
            module="voice",
            device_id=device_id,
            endpoint="/create",
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            request_data=f"text={text[:100]}&voice_code={voice_code}",
            response_status=400,
            response_message=message
        )
        return jsonify(success=False, message=message), 400
    
    host_url = request.host_url.rstrip("/")
    file_url = f"{host_url}/api/voice/play/{file_name}"

    # Log successful voice creation
    db_manager.log_api_usage(
        key_value=key,
        module="voice",
        device_id=device_id,
        endpoint="/create",
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        request_data=f"text={text[:100]}&voice_code={voice_code}",
        response_status=200,
        response_message=f"Voice created: {file_name}"
    )

    return jsonify({
        "success": True,
        "message": message,
        "file_url": file_url,
        "duration": duration
    })


@voice_bp.route("/use", methods=["POST"])
@require_auth(module="voice")
def use_voice_api():
    key = request.form.get("key", "")
    device_id = request.form.get("device_id", "")
    ok, msg = use_voice_key(key, device_id)
    
    # Log usage
    db_manager.log_api_usage(
        key_value=key,
        module="voice",
        device_id=device_id,
        endpoint="/use",
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        request_data=f"key={key}&device_id={device_id}",
        response_status=200 if ok else 400,
        response_message=msg
    )
    
    return jsonify(success=ok, message=msg)

@voice_bp.route("/status", methods=["POST"])
@require_auth(module="voice")
def key_status_api():
    key = request.form.get("key", "")
    device_id = request.form.get("device_id", "")
    
    # Log status check
    db_manager.log_api_usage(
        key_value=key,
        module="voice",
        device_id=device_id,
        endpoint="/status",
        user_ip=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        request_data=f"key={key}&device_id={device_id}",
        response_status=200,
        response_message="Status check"
    )
    
    return jsonify(get_key_status_key(key, device_id))