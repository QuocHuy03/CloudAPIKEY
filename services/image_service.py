import os
from config import IMAGE_OUTPUT_DIR, GEMINI_KEYS_FILE, PROXIES_FILE
from services.key_service_wrapper import update_usage_count, get_key_status, get_key_info, parse_int
from utils.file_utils import create_unique_output_dir, load_proxies
from utils.gemini_client import gemini_image_request
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

def generate_extra_prompt(ratio):
    """Generate extra prompt based on ratio with caching"""
    base_prompts = {
        "9:16": "portrait image, aspect ratio 9:16, suitable for phone wallpapers",
        "6:19": "long cinematic style image, aspect ratio 6:19",
        "1:1": "square image, aspect ratio 1:1, perfect for social media",
    }
    quality_prompt = (
        "high resolution, ultra detailed, sharp focus, "
        "realistic lighting, vibrant colors, professional photography quality, "
        "no artifacts, no blurriness, 4k resolution"
    )
    return f"{base_prompts.get(ratio, '')}, {quality_prompt}"

def create_image(text, key, device_id, ratio="1:1"):
    """Create image with improved performance"""
    api_keys = load_gemini_keys()
    if not api_keys:
        return {"success": False, "message": "No Gemini API key configured"}

    try:
        prompt = text.strip()
        extra_prompt = generate_extra_prompt(ratio)
        if extra_prompt:
            prompt = f"{prompt}, {extra_prompt}"

        output_dir = create_unique_output_dir(IMAGE_OUTPUT_DIR)
        proxies = load_proxies(PROXIES_FILE)
        image_path = gemini_image_request(prompt, output_dir, api_keys, proxies)

        # Update usage count
        update_usage_count(key, device_id, module="image")
        
        filename = os.path.relpath(image_path, IMAGE_OUTPUT_DIR).replace("\\", "/")
        
        # Get key info for message
        info = get_key_info(key, module="image")
        usage_count = parse_int(info.get('usage_count')) if info else None
        max_usage = parse_int(info.get('max_usage')) if info else None

        message = f"🖼️ Đã tạo ảnh ({usage_count}/{max_usage if max_usage else '∞'})"
        return {
            "success": True,
            "message": message,
            "filename": filename
        }
        
    except Exception as e:
        return {"success": False, "message": f"Lỗi tạo ảnh: {e}"}

def use_image_key(key, device_id):
    """Use image key with error handling"""
    try:
        update_usage_count(key, device_id, module="image")
        return True, "✅ Đã trừ lượt thành công"
    except Exception as e:
        return False, str(e)

def get_key_status_key(key, device_id):
    """Get key status for image module"""
    return get_key_status(key, device_id, module="image")

def clear_api_keys_cache():
    """Clear API keys cache"""
    global _api_keys_cache, _api_keys_cache_timestamp
    _api_keys_cache.clear()
    _api_keys_cache_timestamp.clear()
