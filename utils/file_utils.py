import os
import time
import uuid
from functools import lru_cache

# Performance optimizations
_proxy_cache = {}
_proxy_cache_timestamp = {}
PROXY_CACHE_TTL = 300  # Cache proxies for 5 minutes


def ensure_dir(path):
    """Ensure directory exists with better performance"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def create_unique_output_dir(base_dir):
    """Create unique output directory with timestamp and UUID"""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    short_uuid = str(uuid.uuid4())[:8]
    path = os.path.join(base_dir, f"{timestamp}_{short_uuid}")
    ensure_dir(path)
    return path

@lru_cache(maxsize=32)
def _load_proxies_from_file(file_path):
    """Load proxies from file with caching"""
    proxies = []
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, pwd = parts
                        proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
                        proxies.append(proxy_url)
                    else:
                        proxies.append(line)
    except Exception as e:
        print(f"Lỗi đọc file proxy: {e}")
    return proxies

def load_proxies(file_path):
    """Load proxies with intelligent caching"""
    current_time = time.time()
    
    # Check if cache is valid
    if (file_path in _proxy_cache and 
        current_time - _proxy_cache_timestamp.get(file_path, 0) < PROXY_CACHE_TTL):
        return _proxy_cache[file_path]
    
    # Load fresh proxies
    proxies = _load_proxies_from_file(file_path)
    
    # Cache the result
    _proxy_cache[file_path] = proxies
    _proxy_cache_timestamp[file_path] = current_time
    
    return proxies

def clear_proxy_cache():
    """Clear proxy cache"""
    global _proxy_cache, _proxy_cache_timestamp
    _proxy_cache.clear()
    _proxy_cache_timestamp.clear()

def get_file_size(file_path):
    """Get file size efficiently"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def safe_file_operation(func):
    """Decorator for safe file operations"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (OSError, IOError) as e:
            print(f"File operation error: {e}")
            return None
    return wrapper

@safe_file_operation
def read_file_safe(file_path, encoding='utf-8'):
    """Read file safely with error handling"""
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()

@safe_file_operation
def write_file_safe(file_path, content, encoding='utf-8'):
    """Write file safely with error handling"""
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)
