from flask import Blueprint, request, jsonify
import tempfile
import os
from services.clone_voice_service import (
    create_clone_voice,
    get_voice_list,
    text_to_speech,
    get_audio_list,
    get_detail_audio
)
from middlewares.auth import require_auth
from config import VOICE_OUTPUT_DIR
from services.key_service_wrapper import check_key_validity

clone_voice_bp = Blueprint('clone_voice', __name__)

@clone_voice_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        return jsonify(success=False, message="🔒 Thiếu key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="clone_voice")
    if not is_valid:
        return jsonify(success=False, message=msg), 403

    return jsonify(
        success=True,
        message="✅ Xác thực thành công",
        expires=expires if expires else "",
        remaining=remaining
    ), 200

@clone_voice_bp.route("/list_voice", methods=["GET"])
@require_auth(module="clone_voice")
def list_voices_api():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify(success=False, message="❌ Thiếu key"), 400

    voices = get_voice_list(key)
    return jsonify({"success": True, "voices": voices})

@clone_voice_bp.route("/create_clone_voice", methods=["POST"])
@require_auth(module="clone_voice")
def create_voice_api():
    data = request.form
    file = request.files.get("audio_file")

    voice_name = data.get("voice_name", "@huyit32").strip()
    language = data.get("language", "vi").strip()
    gender = data.get("gender", "FEMALE").strip()
    age = data.get("age", "YOUNG").strip()
    key = data.get("key", "").strip()
    device_id = data.get("device_id", "").strip()

    if not file:
        return jsonify(success=False, message="❌ Thiếu audio_file"), 400
    if not key or not device_id:
        return jsonify(success=False, message="❌ Thiếu key hoặc device_id"), 400

    # ✅ Đảm bảo thư mục tồn tại
    os.makedirs(VOICE_OUTPUT_DIR, exist_ok=True)

    # ✅ Lưu file gốc vào VOICE_OUTPUT_DIR
    filename = file.filename
    audio_file_path = os.path.join(VOICE_OUTPUT_DIR, filename)
    file.save(audio_file_path)

    # ✅ Gọi tạo clone voice
    result = create_clone_voice(voice_name, language, gender, age, audio_file_path, key, device_id)

    # ❌ Nếu muốn xóa sau khi dùng → mở dòng này
    os.remove(audio_file_path)

    if not result.get("success"):
        return jsonify(success=False, message=result.get("error", "❌ Tạo clone voice thất bại")), 400

    voice_data = result["data"]
    return jsonify({
        "success": True,
        "message": "✅ Voice clone thành công",
        "data": voice_data
    })

@clone_voice_bp.route("/text_to_voice", methods=["POST"])
def text_to_voice_api():
    try:
        data = request.form
        audio_name = data.get("audio_name", "demo_audio").strip()
        text = data.get("text", "").strip()
        voice_id = data.get("voice_id")
        callback_url = data.get("callback_url", "").strip()
        key = data.get("key", "").strip()
        speed = float(data.get("speed", 1.0))
        model_name = data.get("model_name", "myna-1").strip()
        language = data.get("language")

        # Kiểm tra đầu vào
        if not all([audio_name, text, voice_id, callback_url, key]):
            return jsonify(success=False, message="❌ Thiếu tham số bắt buộc"), 400

        result = text_to_speech(
            audio_name=audio_name,
            text=text,
            voice_id=voice_id,
            callback_url=callback_url,
            key=key,
            speed=speed,
            model_name=model_name,
            language=language
        )

        if not result.get("success"):
            return jsonify(success=False, message=result.get("message", "❌ Tạo audio thất bại")), 400

        return jsonify({
            "success": True,
            "data": result["data"]
        })

    except Exception as e:
        print(f"❌ Exception tại text_to_voice_api: {str(e)}")
        return jsonify(success=False, message=f"❌ Lỗi hệ thống: {str(e)}"), 500

@clone_voice_bp.route('/history_audio_list', methods=["GET"])
@require_auth(module="clone_voice")
def history_audio_list():
    key = request.args.get("key", "").strip()
    if not key:
        return jsonify(success=False, message="❌ Thiếu key"), 400

    audios = get_audio_list(key)
    return jsonify({"success": True, "data": audios})

@clone_voice_bp.route('/history_audio_detail', methods=["GET"])
def detail_audio():
    key = request.args.get("key", "").strip()
    audio_id = request.args.get("audio_id", "").strip()
    if not key or not audio_id:
        return jsonify(success=False, message="❌ Thiếu key hoặc audio_id"), 400

    audios = get_detail_audio(audio_id, key)
    return jsonify({"success": True, "data": audios})

