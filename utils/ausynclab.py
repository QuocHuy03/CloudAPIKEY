import os
import requests
from pydub import AudioSegment

def _ensure_proxies(proxies):
    return proxies if proxies else [None]

def _prepare_audio(audio_file_path):
    if audio_file_path.lower().endswith(".mp3"):
        audio = AudioSegment.from_mp3(audio_file_path)
        wav_path = audio_file_path.rsplit(".", 1)[0] + ".wav"
        audio.export(wav_path, format="wav")
        return wav_path
import time
from pydub import AudioSegment

def _ensure_proxies(proxies):
    """Ensure proxies is always a list"""
    return proxies if proxies else [None]

def _prepare_audio(audio_file_path):
    """Convert MP3 to WAV if needed"""
    if audio_file_path.lower().endswith(".mp3"):
        try:
            audio = AudioSegment.from_mp3(audio_file_path)
            wav_path = audio_file_path.rsplit(".", 1)[0] + ".wav"
            audio.export(wav_path, format="wav")
            return wav_path
        except Exception as e:
            print(f"❌ Lỗi khi convert MP3 sang WAV: {e}")
            return None
    elif audio_file_path.lower().endswith(".wav"):
        return audio_file_path
    else:
        return None

def _safe_request(method, url, headers, proxies, **kwargs):
    for proxy in _ensure_proxies(proxies):
        try:
            resp = requests.request(method, url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, **kwargs)
            print(resp.status_code, resp.text)
            if resp.status_code in [200, 404]:
                return resp
        except Exception:
            continue
    return None

def create_clone_voice_tts(voice_name, language, gender, age, audio_file_path, key, use_case="CASUAL", proxies=None):
    """Create clone voice TTS - placeholder function"""
    pass

def _safe_request(method, url, headers, proxies, **kwargs):
    """Make HTTP request with proxy support and error handling"""
    for proxy in _ensure_proxies(proxies):
        try:
            proxy_dict = {"http": proxy, "https": proxy} if proxy else None
            resp = requests.request(method, url, headers=headers, proxies=proxy_dict, **kwargs)
            print(f"🔍 {method} {url} -> {resp.status_code}")
            print(f"📄 Response: {resp.text[:200]}...")
            
            if resp.status_code in [200, 201, 202]:  # Success codes
                return resp
            elif resp.status_code == 429:  # Rate limit
                print(f"🚥 Rate limit hit: {resp.text}")
                return resp
            elif resp.status_code == 403:  # Parallel limit
                print(f"⛔ Parallel process limit: {resp.text}")
                return resp
            else:
                print(f"⚠️ Unexpected status {resp.status_code}: {resp.text}")
                return resp
                
        except Exception as e:
            print(f"❌ Request error with proxy {proxy}: {e}")
            continue
    
    return None

def create_clone_voice_tts(voice_name, language, gender, age, audio_file_path, key, use_case="CASUAL", proxies=None):
    """Create voice clone with TTS capability"""
    print(f"🎯 Creating voice clone: {voice_name}")
    
    # Prepare audio file
    audio_file_path = _prepare_audio(audio_file_path)
    if not audio_file_path:
        return {"success": False, "error": "❌ File không hợp lệ. Chỉ hỗ trợ mp3 hoặc wav."}

    url = "https://api.ausynclab.org/api/v1/voices/register"
    params = dict(name=voice_name, language=language, gender=gender, age=age, use_case=use_case)
    headers = {"accept": "application/json", "X-API-Key": key}
    files = {"audio_file": (os.path.basename(audio_file_path), open(audio_file_path, "rb"), "audio/wav")}

    resp = _safe_request("POST", url, headers, proxies, params=params, files=files)
    if not resp:
        return {"success": False, "error": "❌ Không thể tạo voice (proxy hoặc API lỗi)."}

    try:
        resp_json = resp.json()
        print(f"Response: {resp_json}")
    except Exception:
        return {"success": False, "error": "❌ Phản hồi không phải JSON."}

    data = resp_json.get("result")
    if not data:
        return {"success": False, "error": f"❌ Phản hồi không chứa result: {resp_json}"}

    voice_id = data.get("id")
    if not voice_id:
        return {"success": False, "error": f"❌ Không tìm thấy voice_id trong result: {data}"}

    data = resp.json().get("result", {})
    voice_id = data.get("id")
    if not voice_id:
        return {"success": False, "error": "❌ Không nhận được voice_id từ phản hồi."}

    detail = get_voice_detail(voice_id, key, proxies)
    return {"success": True, "data": detail.get("data") if detail.get("success") else {}}

def get_voice_detail(voice_id, key, proxies=None):
    url = f"https://api.ausynclab.org/api/v1/voices/{voice_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("GET", url, headers, proxies)
    if resp and resp.status_code == 200:
        return {"success": True, "data": resp.json().get("result")}
    return {"success": False, "error": f"❌ Không lấy được thông tin voice_id={voice_id}"}

def get_voice_list(key, proxies=None):
    url = "https://api.ausynclab.org/api/v1/voices/list"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("GET", url, headers, proxies)
    if resp:
        return {"success": True, "data": resp.json().get("result", [])}
    return {"success": False, "error": "❌ Không thể lấy danh sách voice."}

def delete_voice(voice_id, key, proxies=None):
    url = f"https://api.ausynclab.org/api/v1/voices/{voice_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("DELETE", url, headers, proxies)
    if resp and resp.status_code == 200:
        return {"success": True, "data": resp.json().get("result")}
    return {"success": False, "error": f"❌ Không thể xóa voice_id={voice_id}"}

def text_to_speech(audio_name, text, voice_id, callback_url, key, speed=1.0, model_name="myna-1", language=None, proxies=None, max_retry=10):
    import time

    
    try:
        with open(audio_file_path, "rb") as f:
            files = {"audio_file": (os.path.basename(audio_file_path), f, "audio/wav")}
            resp = _safe_request("POST", url, headers, proxies, params=params, files=files)
    except Exception as e:
        return {"success": False, "error": f"❌ Lỗi khi đọc file audio: {e}"}

    if not resp:
        return {"success": False, "error": "❌ Không thể tạo voice (proxy hoặc API lỗi)."}

    # Handle different response statuses
    if resp.status_code == 429:
        return {"success": False, "error": "🚥 Bị rate limit. Vui lòng thử lại sau."}
    
    if resp.status_code == 403:
        return {"success": False, "error": "⛔ Bị giới hạn parallel process. Vui lòng thử lại sau."}

    try:
        resp_json = resp.json()
        print(f"✅ Voice creation response: {resp_json}")
    except Exception as e:
        return {"success": False, "error": f"❌ Phản hồi không phải JSON: {e}"}

    # Extract voice_id from response
    data = resp_json.get("result", {})
    voice_id = data.get("id")
    
    if not voice_id:
        return {"success": False, "error": f"❌ Không nhận được voice_id từ phản hồi: {resp_json}"}

    print(f"🎉 Voice created successfully with ID: {voice_id}")
    
    # Get voice details
    detail = get_voice_detail(voice_id, key, proxies)
    if detail.get("success"):
        return {"success": True, "data": detail.get("data"), "voice_id": voice_id}
    else:
        return {"success": True, "data": {"voice_id": voice_id}, "warning": "⚠️ Không lấy được chi tiết voice."}

def get_voice_detail(voice_id, key, proxies=None):
    """Get detailed information about a voice"""
    url = f"https://api.ausynclab.org/api/v1/voices/{voice_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("GET", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            data = resp.json().get("result", {})
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ API trả về status {resp.status_code}"}

def get_voice_list(key, proxies=None):
    """Get list of all available voices"""
    url = "https://api.ausynclab.org/api/v1/voices/list"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("GET", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            voices = resp.json().get("result", [])
            print(f"🎵 Found {len(voices)} voices")
            return {"success": True, "data": voices}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ API trả về status {resp.status_code}"}

def delete_voice(voice_id, key, proxies=None):
    """Delete a voice"""
    url = f"https://api.ausynclab.org/api/v1/voices/{voice_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("DELETE", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            result = resp.json().get("result", {})
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ Không thể xóa voice_id={voice_id}, status: {resp.status_code}"}

def text_to_speech(audio_name, text, voice_id, callback_url, key, speed=1.0, model_name="myna-1", language=None, proxies=None, max_retry=10):
    """Convert text to speech with retry logic and queue management"""
    print(f"🎤 Starting TTS: {audio_name} -> {text[:50]}...")
    
    url = "https://api.ausynclab.org/api/v1/speech/text-to-speech"
    headers = {
        "accept": "application/json",
        "X-API-Key": key,
        "Content-Type": "application/json"
    }
    
    data = {
        "audio_name": audio_name,
        "text": text,
        "voice_id": voice_id,
        "callback_url": callback_url,
        "speed": speed,
        "model_name": model_name
    }
    if language:
        data["language"] = language

    for attempt in range(1, max_retry + 1):
        resp = _safe_request("POST", url, headers, proxies, json=data)

    # Retry loop with exponential backoff
    for attempt in range(1, max_retry + 1):
        print(f"🔄 Attempt {attempt}/{max_retry}")
        
        resp = _safe_request("POST", url, headers, proxies, json=data)
        if not resp:
            print(f"❌ Lần {attempt}: Không có phản hồi từ API")
            time.sleep(1.2)
            continue

        try:
            status_code = resp.status_code
            res_json = resp.json()
        except Exception as e:
            return {"success": False, "error": f"❌ Phân tích JSON thất bại: {str(e)}"}

        # 🔁 Nếu bị giới hạn tốc độ
        if status_code == 429:
            print(f"🚥 Lần {attempt}: Bị giới hạn tốc độ – chờ 1.2s trước khi thử lại...")
            time.sleep(1.2)
            continue

        # ✅ Thành công với audio_id
        if status_code == 200 and "result" in res_json:
            result = res_json["result"]
            if "detail" in result and result["detail"].get("error_code") == "parallel_process_limit":
                print(f"⛔ Lần {attempt}: Đang có tác vụ song song – chờ 3s...")
                time.sleep(3)
                continue

            audio_id = result.get("audio_id")
            if not audio_id:
                return {"success": False, "error": "❌ Không có audio_id trong kết quả."}

            detail = get_audio_detail(audio_id, key, proxies)
            return {
                "success": True,
                "data": detail.get("data") if detail.get("success") else {"audio_id": audio_id},
                "warning": None if detail.get("success") else "⚠️ Không lấy được chi tiết audio."
            }

        # ❌ Các lỗi không nằm trong các case trên
        print(f"❌ Lần {attempt}: status {status_code}, nội dung = {res_json}")
        print(f"❌ Lần {attempt}: Lỗi parse JSON: {e}")
        time.sleep(1)
        continue

        # Handle rate limit (429)
        if status_code == 429:
            wait_time = min(1.2 * attempt, 10)  # Exponential backoff, max 10s
            print(f"🚥 Lần {attempt}: Rate limit - chờ {wait_time:.1f}s...")
            time.sleep(wait_time)
            continue

        # Handle parallel process limit (403)
        if status_code == 403:
            error_code = res_json.get("result", {}).get("detail", {}).get("error_code")
            if error_code == "parallel_process_limit":
                wait_time = min(3 * attempt, 15)  # Longer wait for parallel limit
                print(f"⛔ Lần {attempt}: Parallel limit - chờ {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ Lần {attempt}: 403 error - {res_json}")
                time.sleep(1)
                continue

        # Success case
        if status_code == 200 and "result" in res_json:
            result = res_json["result"]
            audio_id = result.get("audio_id")
            
            if not audio_id:
                return {"success": False, "error": "❌ Không có audio_id trong kết quả."}

            print(f"✅ TTS request successful, audio_id: {audio_id}")
            
            # Get audio details
            detail = get_audio_detail(audio_id, key, proxies)
            if detail.get("success"):
                return {
                    "success": True, 
                    "data": detail.get("data"),
                    "audio_id": audio_id
                }
            else:
                return {
                    "success": True, 
                    "data": {"audio_id": audio_id},
                    "warning": "⚠️ Không lấy được chi tiết audio."
                }

        # Other error cases
        print(f"❌ Lần {attempt}: Status {status_code}, Response: {res_json}")
        time.sleep(1)

    return {"success": False, "error": f"❌ Quá số lần thử ({max_retry}), vẫn bị rate limit hoặc lỗi khác."}

def get_audio_list(key, proxies=None):
    url = "https://api.ausynclab.org/api/v1/speech/"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("GET", url, headers, proxies)
    if resp:
        return {"success": True, "data": resp.json().get("result", [])}
    return {"success": False, "error": "❌ Không thể lấy danh sách audio."}

def get_audio_detail(audio_id, key, proxies=None):
    url = f"https://api.ausynclab.org/api/v1/speech/{audio_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("GET", url, headers, proxies)
    if resp and resp.status_code == 200:
        return {"success": True, "data": resp.json().get("result")}
    return {"success": False, "error": f"❌ Không lấy được chi tiết audio_id={audio_id}"}

def delete_audio(audio_id, key, proxies=None):
    url = f"https://api.ausynclab.org/api/v1/speech/{audio_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    resp = _safe_request("DELETE", url, headers, proxies)
    if resp and resp.status_code == 200:
        return {"success": True, "data": resp.json().get("result")}
    return {"success": False, "error": f"❌ Không thể xóa audio_id={audio_id}"}
def get_audio_list(key, proxies=None):
    """Get list of all audio files"""
    url = "https://api.ausynclab.org/api/v1/speech/"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("GET", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            audio_list = resp.json().get("result", [])
            print(f"🎵 Found {len(audio_list)} audio files")
            return {"success": True, "data": audio_list}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ API trả về status {resp.status_code}"}

def get_audio_detail(audio_id, key, proxies=None):
    """Get detailed information about an audio file"""
    url = f"https://api.ausynclab.org/api/v1/speech/{audio_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("GET", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            data = resp.json().get("result", {})
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ Không lấy được chi tiết audio_id={audio_id}, status: {resp.status_code}"}

def delete_audio(audio_id, key, proxies=None):
    """Delete an audio file"""
    url = f"https://api.ausynclab.org/api/v1/speech/{audio_id}"
    headers = {"accept": "application/json", "X-API-Key": key}
    
    resp = _safe_request("DELETE", url, headers, proxies)
    if not resp:
        return {"success": False, "error": "❌ Không thể kết nối API"}
    
    if resp.status_code == 200:
        try:
            result = resp.json().get("result", {})
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": f"❌ Lỗi parse JSON: {e}"}
    else:
        return {"success": False, "error": f"❌ Không thể xóa audio_id={audio_id}, status: {resp.status_code}"}
