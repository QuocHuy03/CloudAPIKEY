from flask import Blueprint, request, jsonify
from services.music_service import create_music, get_task_status
from middlewares.auth import require_auth
from services.key_service_wrapper import check_key_validity
from services.key_service import check_key_validity

music_bp = Blueprint('music', __name__)

def validate_field(field_name, value):
    """Helper function to validate non-empty required fields."""
    if not value:
        return jsonify(success=False, message=f"❌ Thiếu {field_name}"), 400
    return None

@music_bp.route("/auth", methods=["POST"])
def auth_api():
    key = request.form.get("key", "").strip()
    device_id = request.form.get("device_id", "").strip()

    if not key or not device_id:
        return jsonify(success=False, message="🔒 Thiếu key hoặc device_id"), 400

    is_valid, msg, expires, remaining = check_key_validity(key, device_id, module="music")
    if not is_valid:
        return jsonify(success=False, message=msg), 403

    return jsonify(
        success=True,
        message="✅ Xác thực thành công",
        expires=expires.strftime("%Y-%m-%d") if expires else "",
        remaining=remaining
    ), 200

@music_bp.route("/create_music", methods=["POST"])
@require_auth(module="music")
def create_music_api():
    data = request.form
    # Extract form data with validations
    prompt_text = data.get("prompt_text", "").strip()
    title = data.get("title", "").strip()
    style = data.get("style", "").strip()
    instrumental = data.get("instrumental", "true").strip()  # Default value is "true"
    key = data.get("key", "").strip()
    device_id = data.get("device_id", "").strip()

    # Validate required fields using helper function
    validation_error = validate_field("prompt_text (Mô tả nhạc hoặc lời bài hát)", prompt_text)
    if validation_error: return validation_error

    validation_error = validate_field("title (Tiêu đề nhạc)", title)
    if validation_error: return validation_error

    validation_error = validate_field("style (Thể loại nhạc)", style)
    if validation_error: return validation_error

    if not key or not device_id:
        return jsonify(success=False, message="❌ Thiếu key hoặc device_id"), 400

    # Validate instrumental value (should be 'true' or 'false')
    if instrumental not in ['True', 'False']:
        return jsonify(success=False, message="❌ Giá trị của instrumental phải là 'true' hoặc 'false'"), 200

    try:
        # Call create_music to generate music or clone voice
        result = create_music(prompt_text, title, style, instrumental, key, device_id)
        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result), 200
    except Exception as e:
        return jsonify(success=False, message=f"❌ Lỗi khi tạo nhạc: {str(e)}"), 500

@music_bp.route("/get_task", methods=["GET"])
@require_auth(module="music")
def get_task_api():
    task_id = request.args.get("task_id", "").strip()
    key = request.args.get("key", "").strip()
    api_key = request.args.get("api_key", "").strip()

    if not task_id or not key:
        return jsonify(success=False, message="❌ Thiếu task_id hoặc key"), 400

    if not api_key:
        return jsonify(success=False, message="❌ Invalid api_key"), 403

    try:
        # Call get_task_status to retrieve task details
        result = get_task_status(task_id, api_key)
        if not result.get("success"):
            return jsonify(result), 200
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        
        return jsonify(success=False, message=f"❌ Lỗi khi lấy thông tin task: {str(e)}"), 500
