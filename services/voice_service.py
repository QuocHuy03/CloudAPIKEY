import os
from config import VOICE_OUTPUT_DIR, GEMINI_KEYS_FILE, PROXIES_FILE
from services.key_service_wrapper import update_usage_count, get_key_status, get_key_info, parse_int
from services.key_service import update_usage_count, get_key_status, get_key_info, parse_int
from utils.file_utils import create_unique_output_dir, load_proxies
from utils.gemini_client import gemini_tts_request
import time

# Performance optimizations
_api_keys_cache = {}
_api_keys_cache_timestamp = {}
API_KEYS_CACHE_TTL = 300  # Cache API keys for 5 minutes

def load_gemini_keys():
    """Load Gemini API keys with caching"""
    current_time = time.time()
    
    # Check if cache is valid
    if (GEMINI_KEYS_FILE in _api_keys_cache and 
        current_time - _api_keys_cache_timestamp.get(GEMINI_KEYS_FILE, 0) < API_KEYS_CACHE_TTL):
        return _api_keys_cache[GEMINI_KEYS_FILE]
    
    # Load fresh keys
    if not os.path.exists(GEMINI_KEYS_FILE):
        return []
    
    try:
        with open(GEMINI_KEYS_FILE, 'r', encoding='utf-8') as f:
            keys = [l.strip() for l in f if l.strip()]
        
        # Cache the result
        _api_keys_cache[GEMINI_KEYS_FILE] = keys
        _api_keys_cache_timestamp[GEMINI_KEYS_FILE] = current_time
        
        return keys
    except Exception as e:
        print(f"Error loading Gemini keys: {e}")
        return []

def create_voice(text, key, device_id, voice_code="achird"):
    """Create voice with improved performance"""
    api_keys = load_gemini_keys()
    if not api_keys:
        return {"success": False, "message": "No Gemini API key configured"}

    output_dir = create_unique_output_dir(VOICE_OUTPUT_DIR)
    proxies = load_proxies(PROXIES_FILE)
    mp3_path, duration = gemini_tts_request(text, voice_code, output_dir, api_keys, proxies)

    try:
        output_dir = create_unique_output_dir(VOICE_OUTPUT_DIR)
        proxies = load_proxies(PROXIES_FILE)
        mp3_path, duration = gemini_tts_request(text, voice_code, output_dir, api_keys, proxies)

        # Update usage count
        update_usage_count(key, device_id, module="voice")
        
        filename = os.path.relpath(mp3_path, VOICE_OUTPUT_DIR).replace("\\", "/")
        
        # Get key info for message
        info = get_key_info(key, module="voice")
        usage_count = parse_int(info.get('usage_count')) if info else None
        max_usage = parse_int(info.get('max_usage')) if info else None

        message = f"✅ Voice created ({usage_count}/{max_usage if max_usage else '∞'})"
        return True, message, filename, duration
        
    except Exception as e:
        return {"success": False, "message": str(e)}

def use_voice_key(key, device_id):
    """Use voice key with error handling"""
    try:
        update_usage_count(key, device_id, module="voice")
        return True, "✅ Đã trừ lượt thành công"
    except Exception as e:
        return False, str(e)

def get_voice_list(base_url=None):
    """Get voice list with sample URLs"""
    voices = [
        {"name": "Voice 1 - Alpha", "code": "achernar"},
        {"name": "Voice 2 - Beta", "code": "achird"},
        {"name": "Voice 3 - Gamma", "code": "algenib"},
        {"name": "Voice 4 - Delta", "code": "algieba"},
        {"name": "Voice 5 - Epsilon", "code": "alnilam"},
        {"name": "Voice 6 - Zeta", "code": "aoede"},
        {"name": "Voice 7 - Eta", "code": "autonoe"},
        {"name": "Voice 8 - Theta", "code": "callirrhoe"},
        {"name": "Voice 9 - Iota", "code": "charon"},
        {"name": "Voice 10 - Kappa", "code": "despina"},
        {"name": "Voice 11 - Lambda", "code": "enceladus"},
        {"name": "Voice 12 - Mu", "code": "erinome"},
        {"name": "Voice 13 - Nu", "code": "fenrir"},
        {"name": "Voice 14 - Xi", "code": "gacrux"},
        {"name": "Voice 15 - Omicron", "code": "iapetus"},
        {"name": "Voice 16 - Pi", "code": "kore"},
        {"name": "Voice 17 - Rho", "code": "laomedeia"},
        {"name": "Voice 18 - Sigma", "code": "leda"},
        {"name": "Voice 19 - Tau", "code": "orus"},
        {"name": "Voice 20 - Upsilon", "code": "puck"},
        {"name": "Voice 21 - Phi", "code": "pulcherrima"},
        {"name": "Voice 22 - Chi", "code": "rasalgethi"},
        {"name": "Voice 23 - Psi", "code": "sadachbia"},
        {"name": "Voice 24 - Omega", "code": "sadaltager"},
        {"name": "Voice 25 - Alpha Prime", "code": "schedar"},
        {"name": "Voice 26 - Beta Prime", "code": "sulafat"},
        {"name": "Voice 27 - Gamma Prime", "code": "umbriel"},
        {"name": "Voice 28 - Delta Prime", "code": "vindemiatrix"},
        {"name": "Voice 29 - Epsilon Prime", "code": "zephyr"},
        {"name": "Voice 30 - Zeta Prime", "code": "zubenelgenubi"},
    ]

    if base_url:
        for voice in voices:
            filename = f"{voice['code']}.mp3"
            file_path = os.path.join(VOICE_OUTPUT_DIR, filename)

            if os.path.exists(file_path):
                voice["sample_url"] = f"{base_url}/api/voice/play/{filename}"
            else:
                voice["sample_url"] = None

    return voices

def get_key_status_key(key, device_id):
    """Get key status for voice module"""
    return get_key_status(key, device_id, module="voice")

def clear_api_keys_cache():
    """Clear API keys cache"""
    global _api_keys_cache, _api_keys_cache_timestamp
    _api_keys_cache.clear()
    _api_keys_cache_timestamp.clear()
