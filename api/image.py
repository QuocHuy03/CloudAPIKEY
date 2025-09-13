from flask import Blueprint, request, jsonify, send_from_directory
from services.image_service import (
    create_image, use_image_key, get_key_status_key
)
from services.key_service_wrapper import check_key_validity
from middlewares.auth import require_auth
from database import db_manager
import os

image_bp = Blueprint('image', __name__)

@image_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        return jsonify(success=False, message="🔒 Thiếu trường key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="image")
    if not is_valid:
        # Log failed authentication
        db_manager.log_api_usage(
            key_value=key,
            module="image",
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
        module="image",
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


@image_bp.route("/play/<path:filename>")
def serve_image_sample(filename):
    return send_from_directory("images", filename)


@image_bp.route("/create", methods=["POST"])
@require_auth(module="image")
def create_image_api():
    data = request.form
    text = data.get("text", "").strip()
    key = data.get("key", "").strip()
    device_id = data.get("device_id", "").strip()
    ratio = data.get("ratio", "").strip()
    style = data.get("style", "").strip()
    theme = data.get("theme", "").strip()
    mood = data.get("mood", "").strip()
    lighting = data.get("lighting", "").strip()
    detail_level = data.get("detail_level", "").strip()

    if not text:
        return jsonify(success=False, message="❌ Thiếu text"), 400 
    if not ratio:
        return jsonify(success=False, message="❌ Thiếu ratio"), 400
    if not key or not device_id:
        return jsonify(success=False, message="❌ Thiếu key hoặc device_id"), 400


     # Gộp các phần prompt lại
    prompt_parts = [
        text,
        f"Style: {style}" if style else "",
        f"Theme: {theme}" if theme else "",
        f"Mood: {mood}" if mood else "",
        f"Lighting: {lighting}" if lighting else "",
        f"Detail level: {detail_level}" if detail_level else "",
    ]
    full_prompt = ". ".join([p for p in prompt_parts if p])
    


    result = create_image(full_prompt, key, device_id, ratio)
    if not result.get("success"):
        return jsonify(success=False, message=result.get("message")), 400

    filename = result.get("filename")
    message = result.get("message")
    success = result.get("success")

    host_url = request.host_url.rstrip("/")
    file_url = f"{host_url}/api/image/play/{filename}"

    return jsonify({
        "success": success,
        "message": message,
        "file_url": file_url,
    })



@image_bp.route("/use", methods=["POST"])
@require_auth(module="image")
def use_image_api():
    key = request.form.get("key", "")
    device_id = request.form.get("device_id", "")
    ok, msg = use_image_key(key, device_id)
    return jsonify(success=ok, message=msg)


@image_bp.route("/status", methods=["POST"])
@require_auth(module="image")
def key_status_api():
    key = request.form.get("key", "")
    device_id = request.form.get("device_id", "")
    return jsonify(get_key_status_key(key, device_id))