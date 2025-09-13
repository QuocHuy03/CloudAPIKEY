import os
import time  # <- bổ sung

from config import PROXIES_FILE
from utils.file_utils import load_proxies
from services.key_service_wrapper import update_usage_count_by
from utils.ausynclab import (
    create_clone_voice_tts,
    get_voice_list as ausync_get_voice_list,
    text_to_speech as ausync_text_to_speech,
    get_audio_list as ausync_get_audio_list,
    get_audio_detail as ausync_get_audio_detail,
)

def _get_proxies():
    return load_proxies(PROXIES_FILE)

def create_clone_voice(voice_name, language, gender, age, audio_file_path, key, device_id=None):
    result = create_clone_voice_tts(
        voice_name=voice_name,
        language=language,
        gender=gender,
        age=age,
        audio_file_path=audio_file_path,
        key=key,
        proxies=_get_proxies()
    )
    return result

def get_voice_list(key):
    result = ausync_get_voice_list(key, proxies=_get_proxies())
    return result["data"] if result.get("success") else []

def get_detail_audio(audio_id, key):
    result = ausync_get_audio_detail(audio_id, key, proxies=_get_proxies())
    return result["data"] if result.get("success") else None

def get_audio_list(key):
    result = ausync_get_audio_list(key, proxies=_get_proxies())
    return result["data"] if result.get("success") else []

def text_to_speech(audio_name, text, voice_id, callback_url, key, device_id=None, speed=1.0, model_name="myna-1", language=None):
    """
    Gọi API text-to-speech của AusyncLab để tạo giọng nói từ văn bản.
    - Giới hạn tối đa 500 ký tự.
    - Tính số lượt sử dụng chính xác theo độ dài văn bản.
    - Tự động đợi đến khi job hoàn tất nếu trả về IN_PROGRESS.
    - Có try/catch bao toàn bộ để báo lỗi rõ ràng.
    """
    try:
        text_length = len(text)
        if text_length > 500:
            return {
                "success": False,
                "message": f"❌ Văn bản quá dài ({text_length} ký tự). Giới hạn tối đa là 500 ký tự."
            }

        count = text_length
        print(f"📝 Text length: {text_length} ký tự -> Trừ {count} lượt")

        result = ausync_text_to_speech(
            audio_name=audio_name,
            text=text,
            voice_id=voice_id,
            callback_url=callback_url,
            key=key,
            speed=speed,
            model_name=model_name,
            language=language,
            proxies=_get_proxies()
        )

        if not result.get("success"):
            print(f"⚠️ API trả về lỗi: {result}")
            return {
                "success": False,
                "message": result.get("message") or result.get("error") or "Lỗi không xác định từ API"
            }

        data = result.get("data")
        if not data:
            return {
                "success": False,
                "message": "❌ API không trả về dữ liệu audio"
            }

        task_id = data.get("id")
        print(f"🎤 Job ID: {task_id}, voice: {data.get('voice_name')}, state: {data.get('state')}")

        while data.get("state") == "IN_PROGRESS":
            time.sleep(2)
            data = get_detail_audio(task_id, key)
            if not data:
                return {
                    "success": False,
                    "message": "❌ Không kiểm tra được trạng thái task"
                }
            print(f"⏳ Đang xử lý... state = {data.get('state')}")

        if data.get("state") == "SUCCEED":
            
            update_usage_count_by(key, count=count, device_id=device_id, module="clone_voice")
            print(f"✅ Hoàn tất! audio_url = {data.get('audio_url')}")
            return {
                "success": True,
                "data": data
            }
        else:
            return {
                "success": False,
                "message": f"❌ Voice tạo thất bại. Trạng thái cuối cùng: {data.get('state')}"
            }

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {
            "success": False,
            "message": f"Lỗi hệ thống: {str(e)}"
        }

def use_voice_key(key, device_id):
    try:
        update_usage_count_by(key, count=1, device_id=device_id, module="clone_voice")
        return True, "✅ Đã trừ lượt thành công"
    except Exception as e:
        return False, str(e)
