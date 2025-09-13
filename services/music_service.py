import os
import logging
from config import SUDO_KEYS_FILE, PROXIES_FILE
from services.key_service_wrapper import update_usage_count, get_key_status
from utils.file_utils import load_proxies
from utils.suno import generate_music, check_task_status
from services.key_service import update_usage_count, get_key_status
from utils.file_utils import load_proxies
from utils.suno import generate_music, check_task_status
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Performance optimizations
_api_keys_cache = {}
_api_keys_cache_timestamp = {}
API_KEYS_CACHE_TTL = 300  # Cache API keys for 5 minutes

def load_sudo_keys():
    """Load Sudo API keys with caching"""
    current_time = time.time()
    
    # Check if cache is valid
    if (SUDO_KEYS_FILE in _api_keys_cache and 
        current_time - _api_keys_cache_timestamp.get(SUDO_KEYS_FILE, 0) < API_KEYS_CACHE_TTL):
        return _api_keys_cache[SUDO_KEYS_FILE]
    
    # Load fresh keys
    if not os.path.exists(SUDO_KEYS_FILE):
        logging.warning(f"Sudo keys file '{SUDO_KEYS_FILE}' not found.")
        return []
    
    try:
        with open(SUDO_KEYS_FILE) as f:
            keys = [l.strip() for l in f if l.strip()]
        if not keys:
            logging.warning("No valid keys found in the Sudo keys file.")
        with open(SUDO_KEYS_FILE, 'r', encoding='utf-8') as f:
            keys = [l.strip() for l in f if l.strip()]
        
        if not keys:
            logging.warning("No valid keys found in the Sudo keys file.")
        
        # Cache the result
        _api_keys_cache[SUDO_KEYS_FILE] = keys
        _api_keys_cache_timestamp[SUDO_KEYS_FILE] = current_time
        
        return keys
    except Exception as e:
        logging.error(f"Error loading Sudo keys: {e}")
        return []

def create_music(prompt_text, title, style, instrumental, key, device_id):
    """Create music with improved performance"""
    api_keys = load_sudo_keys()
    if not api_keys:
        return {"success": False, "message": "No Sudo API key configured"}
    
    proxies = load_proxies(PROXIES_FILE)
    if not proxies:
        logging.warning(f"Proxies file '{PROXIES_FILE}' is empty or not found. Proceeding without proxies.")
    
    result_data = generate_music(prompt_text, title, style, instrumental, api_keys, proxies)
    print(result_data)
    
    # Kiểm tra xem kết quả có thành công hay không
    if not result_data or result_data.get("success") is False:
        # Log thông báo lỗi nếu không thành công
        message = result_data.get("message", "Music generation failed.")
        print(f"Music generation failed: {message}")
        return {"success": False, "message": message}
    
    # Chỉ khi thành công mới trừ số lần sử dụng
    try:
        update_usage_count(key, device_id, module="music")
    except Exception as e:
        logging.error(f"Error updating usage count: {e}")
        return {"success": False, "message": f"Error updating usage count: {str(e)}"}
    
    return result_data

def get_key_status_key(key, device_id):

    try:
        result_data = generate_music(prompt_text, title, style, instrumental, api_keys, proxies)
        
        # Check if result is successful
        if not result_data or result_data.get("success") is False:
            message = result_data.get("message", "Music generation failed.") if result_data else "Music generation failed."
            logging.error(f"Music generation failed: {message}")
            return {"success": False, "message": message}
        
        # Update usage count only on success
        update_usage_count(key, device_id, module="music")
        return result_data
        
    except Exception as e:
        logging.error(f"Error in create_music: {e}")
        return {"success": False, "message": f"Error creating music: {str(e)}"}

def get_key_status_key(key, device_id):
    """Get key status for music module"""
    try:
        return get_key_status(key, device_id, module="music")
    except Exception as e:
        logging.error(f"Error getting key status: {e}")
        return {"success": False, "message": f"Error getting key status: {str(e)}"}

# Renaming the second function to get_task_status to avoid conflicts
def get_task_status(task_id, api_key):
    proxies = load_proxies(PROXIES_FILE)
    try:
        return check_task_status(task_id, api_key)
    except Exception as e:
        logging.error(f"Error getting task status: {e}")
        return {"success": False, "message": f"Error getting task status: {str(e)}"}
def get_task_status(task_id, api_key):
    """Get task status with error handling"""
    try:
        proxies = load_proxies(PROXIES_FILE)
        return check_task_status(task_id, api_key, proxies)
    except Exception as e:
        logging.error(f"Error getting task status: {e}")
        return {"success": False, "message": f"Error getting task status: {str(e)}"}

def clear_api_keys_cache():
    """Clear API keys cache"""
    global _api_keys_cache, _api_keys_cache_timestamp
    _api_keys_cache.clear()
    _api_keys_cache_timestamp.clear()
