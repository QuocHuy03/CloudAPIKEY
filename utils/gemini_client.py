import requests
import base64
import os
import random
import time
import ffmpeg
from mutagen.mp3 import MP3
from requests.exceptions import SSLError, Timeout, ProxyError, ConnectionError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache

# Performance optimizations
_session_cache = {}
_session_cache_timestamp = {}
SESSION_CACHE_TTL = 600  # Cache sessions for 10 minutes

def create_session_with_retry():
    """Create requests session with retry strategy and connection pooling"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Configure adapter with connection pooling
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def get_session(proxy_dict=None):
    """Get or create session with caching"""
    cache_key = str(proxy_dict) if proxy_dict else "default"
    current_time = time.time()
    
    # Check if cache is valid
    if (cache_key in _session_cache and 
        current_time - _session_cache_timestamp.get(cache_key, 0) < SESSION_CACHE_TTL):
        return _session_cache[cache_key]
    
    # Create new session
    session = create_session_with_retry()
    _session_cache[cache_key] = session
    _session_cache_timestamp[cache_key] = current_time
    
    return session

def get_audio_duration(file_path):
    """Get audio duration with better error handling"""
    try:
        return round(MP3(file_path).info.length, 2)
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def gemini_tts_request(text, voice_name, output_dir, api_key_list, proxies=None):
    """Generate TTS with improved performance and error handling"""
    if proxies is None or not proxies:
        proxies = [None]

    def task(api_key, proxy_dict):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
            headers = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice_name
                            }
                        }
                    }
                },
                "model": "gemini-2.5-flash-preview-tts",
            }

            session = get_session(proxy_dict)
            response = session.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"Lỗi HTTP {response.status_code} từ Gemini: {response.text[:300]}")

            res_json = response.json()
            audio_data = res_json['candidates'][0]['content']['parts'][0]['inlineData']['data']

            uid = f"{int(time.time())}_{random.randint(1000,9999)}"
            temp_pcm = os.path.join(output_dir, f"{uid}.pcm")
            
            with open(temp_pcm, "wb") as f:
                f.write(base64.b64decode(audio_data))

            mp3_file = os.path.join(output_dir, f"{uid}.mp3")
            try:
                ffmpeg.input(temp_pcm, f='s16le', ar='24000', ac='1') \
                    .output(mp3_file, **{'y': None}) \
                    .run(overwrite_output=True, quiet=True)
                os.remove(temp_pcm)
                duration = get_audio_duration(mp3_file)
            except Exception as e:
                raise Exception(f"Lỗi convert hoặc đo thời lượng: {e}")

            return mp3_file, duration

        except Exception as e:
            print(f"Key {api_key[:20]} lỗi: {e}")
            return None

    # Phân chia proxy theo key
    # Try each API key with proxy rotation
    for i, api_key in enumerate(api_key_list):
        proxy_str = proxies[i % len(proxies)]
        proxy_dict = {"http": proxy_str, "https": proxy_str} if proxy_str else None
        print(f"[VOICE] Thử key {i+1}/{len(api_key_list)}: {api_key[:20]} với proxy: {proxy_str}")
        result = task(api_key, proxy_dict)
        if result:
            return result

    raise Exception("Không có key nào khả dụng để tạo voice.")

def gemini_image_request(prompt_text, output_dir, api_key_list, proxies=None):
    """Generate image with improved performance and error handling"""
    if proxies is None or not proxies:
        proxies = [None]

    print(f"🛠️ Proxies được truyền vào: {proxies}")

    def task(api_key, proxy_dict):
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent"
            headers = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "contents": [{
                    "parts": [{"text": prompt_text}]
                }],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            }

            print(f"🚀 Đang gọi API với key: {api_key[:20]}..., proxy: {proxy_dict}")

            session = get_session(proxy_dict)
            response = session.post(url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                raise Exception(f"❌ HTTP {response.status_code}: {response.text[:300]}")

            res_json = response.json()
            parts = res_json.get("candidates", [])[0].get("content", {}).get("parts", [])
            image_part = next((p for p in parts if "inlineData" in p and "image" in p["inlineData"]["mimeType"]), None)

            if not image_part:
                raise Exception("⚠️ Không tìm thấy dữ liệu hình ảnh trong response.")

            uid = f"{int(time.time())}_{random.randint(1000,9999)}"
            image_path = os.path.join(output_dir, f"{uid}.png")
            
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_part["inlineData"]["data"]))

            print(f"✅ Tạo ảnh thành công: {image_path}")
            return image_path

        except SSLError as e:
            print(f"❌ SSL Error với key {api_key[:20]}: {e}")
        except Timeout:
            print(f"⏳ Timeout với key {api_key[:20]}")
        except ProxyError as e:
            print(f"🔌 Proxy Error với key {api_key[:20]}: {e}")
        except ConnectionError as e:
            print(f"📡 Lỗi kết nối với key {api_key[:20]}: {e}")
        except Exception as e:
            print(f"🔥 Key {api_key[:20]} lỗi khác: {e}")

        return None

    # 🔄 Duyệt từng key với proxy tương ứng
    for i, api_key in enumerate(api_key_list):
        proxy_str = proxies[i % len(proxies)]
        proxy_dict = {"http": proxy_str, "https": proxy_str} if proxy_str else None
        print(f"[IMAGE] ⚙️ Thử key {i+1}/{len(api_key_list)} với proxy: {proxy_str}")
        result = task(api_key, proxy_dict)
        if result:
            return result

    raise Exception("🚫 Không có key nào khả dụng để tạo ảnh.")

def clear_session_cache():
    """Clear session cache"""
    global _session_cache, _session_cache_timestamp
    _session_cache.clear()
    _session_cache_timestamp.clear()
