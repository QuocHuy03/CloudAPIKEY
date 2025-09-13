import pandas as pd
from config import csv_lock
from datetime import datetime
import time

# Performance optimizations
_key_cache = {}
_key_cache_timestamp = {}
KEY_CACHE_TTL = 60  # Cache key validation for 60 seconds

def get_csv_file(module=None):
    """Get CSV file path - deprecated, using SQL database"""
    return None

def parse_int(i):
    """Parse integer with better error handling"""
    if pd.isna(i) or i == '':
        return None
    try:
        return int(float(i))
    except (ValueError, TypeError):
        return None

def get_key_info(key, module=None):
    """Get key info with caching"""
    cache_key = f"{key}_{module}"
    current_time = time.time()
    
    # Check cache first
    if (cache_key in _key_cache and 
        current_time - _key_cache_timestamp.get(cache_key, 0) < KEY_CACHE_TTL):
        return _key_cache[cache_key]
    
    df = get_csv_data(module)
    if df is None:
        return None
    
    row = df.loc[df['key'] == key]
    if row.empty:
        return None
    
    result = row.iloc[0].to_dict()
    
    # Cache the result
    _key_cache[cache_key] = result
    _key_cache_timestamp[cache_key] = current_time
    
    return result

def parse_date(d):
    """Parse date with better error handling"""
    if pd.isna(d) or not d:
        return None
    
    # Try common date formats
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%d/%m/%y"]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(d).strip(), fmt)
        except ValueError:
            continue
    
    return None


def parse_date(d):
    if pd.isna(d) or not d:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):  # Thêm định dạng %m/%d/%y để hỗ trợ MM/DD/YY
        try:
            return datetime.strptime(str(d), fmt)
        except ValueError:
            continue
    return None

def check_key_validity(key, device_id, module=None):
    """Check key validity with improved performance"""
    df = get_csv_data(module)
    if df is None:
        return False, "📄 Không thể đọc file dữ liệu!", None, None

    # Find the key row efficiently
    key_mask = df['key'] == key
    if not key_mask.any():
        return False, "❌ KEY không tồn tại!", None, None

    row = df[key_mask].iloc[0]
    idx = df[key_mask].index[0]
    info = row.to_dict()

    # Kiểm tra nếu device_id đã gán cho key khác
    for _, row in df.iterrows():
        row_device = str(row.get("device_id", "")).strip()
        row_key = str(row.get("key", "")).strip()
        if row_device and row_device == device_id and row_key != key:
            print(f"[BLOCK] Thiết bị {device_id} đã được gán với KEY khác: {row_key}")
            return False, f"❌ Thiết bị này đã được dùng với KEY khác ({row_key})!", None, None
    
    # Check status
    if str(info.get('status', '')).strip().lower() != "active":
        return False, "🔒 KEY bị khóa", None, None

    # Check expiration
    expires = parse_date(info.get('expires'))
    if not expires:
        return False, "❌ KEY không có hạn sử dụng", None, None
    
    if expires < datetime.now():
        return False, "⏳ KEY đã hết hạn sử dụng", expires, None

    # Check device ID binding
    current_device = str(info.get('device_id', '')).strip()
    if not current_device:
        # Bind new device
        print(f"[GÁN DEVICE] KEY={key} chưa có device_id, gán: {device_id}")
        with csv_lock:
            df.at[idx, 'device_id'] = device_id
            df.to_csv(get_csv_file(module), index=False)
            # Clear cache to reflect changes
            clear_csv_cache(module)
    elif current_device != device_id:
        return False, "📵 KEY đã bị gán với thiết bị khác!", expires, None

    # Check usage limits
    max_usage = parse_int(info.get('max_usage'))
    usage_count = parse_int(info.get('usage_count'))

    remaining = "unlimited"
    if max_usage is not None and usage_count is not None:
        if usage_count >= max_usage:
            return False, f"🚫 Đã dùng hết lượt ({usage_count}/{max_usage})", expires, 0
        remaining = max_usage - usage_count

    return True, "OK", expires, remaining

def update_usage_count(key, device_id=None, module=None):
    """Update usage count with better performance"""
    csv_file = get_csv_file(module)
    if not csv_file:
        raise Exception("❌ Module không hợp lệ")

    with csv_lock:
        df = get_csv_data(module, force_refresh=True)  # Force refresh to get latest data
        
        row = df.loc[df['key'] == key]
        if row.empty:
            raise Exception("Key không tồn tại")
        idx = row.index[0]

        if device_id:
            saved = df.at[idx, 'device_id']
            if pd.isna(saved) or not str(saved).strip():
                df.at[idx, 'device_id'] = device_id
            elif str(saved).strip() != device_id:
                raise Exception("📵 KEY đã bị gán với thiết bị khác")

        usage = parse_int(df.at[idx, 'usage_count']) or 0
        maxu = parse_int(df.at[idx, 'max_usage'])
        
        if maxu is not None and usage >= maxu:
            raise Exception(f"🚫 Đã dùng hết lượt ({usage}/{maxu})")

        df.at[idx, 'usage_count'] = usage + 1
        df.to_csv(csv_file, index=False)
        
        # Clear cache to reflect changes
        clear_csv_cache(module)

def update_usage_count_by(key, count, device_id=None, module=None):
    """Update usage count by specific amount"""
    if not isinstance(count, int) or count <= 0:
        raise Exception("❌ Giá trị 'count' phải là số nguyên dương")

    csv_file = get_csv_file(module)
    if not csv_file:
        raise Exception("❌ Module không hợp lệ")

    with csv_lock:
        df = get_csv_data(module, force_refresh=True)
        
        row = df.loc[df['key'] == key]
        if row.empty:
            raise Exception("❌ KEY không tồn tại")
        idx = row.index[0]

        if device_id:
            saved = df.at[idx, 'device_id']
            if pd.isna(saved) or not str(saved).strip():
                df.at[idx, 'device_id'] = device_id
            elif str(saved).strip() != device_id:
                raise Exception("📵 KEY đã bị gán với thiết bị khác")

        usage = parse_int(df.at[idx, 'usage_count']) or 0
        maxu = parse_int(df.at[idx, 'max_usage'])
        
        if maxu is not None and usage + count > maxu:
            raise Exception(f"🚫 Vượt quá số lượt cho phép ({usage + count}/{maxu})")

        df.at[idx, 'usage_count'] = usage + count
        df.to_csv(csv_file, index=False)
        
        # Clear cache to reflect changes
        clear_csv_cache(module)

def update_usage_count_by(key, count, device_id=None, module=None):
    if not isinstance(count, int) or count <= 0:
        raise Exception("❌ Giá trị 'count' phải là số nguyên dương")

    csv_file = get_csv_file(module)
    if not csv_file:
        raise Exception("❌ Module không hợp lệ")

    with csv_lock:
        df = pd.read_csv(csv_file)
        
        row = df.loc[df['key'] == key]
        if row.empty:
            raise Exception("❌ KEY không tồn tại")
        idx = row.index[0]

        if device_id:
            saved = df.at[idx, 'device_id']
            if pd.isna(saved) or not str(saved).strip():
                print(f"📲 GÁN KEY mới: '{key}' -> device_id: {device_id}")
                df.at[idx, 'device_id'] = device_id
            elif str(saved).strip() != device_id:
                print(f"📵 TỪ CHỐI: KEY '{key}' đã gán device_id: {saved}, client gửi: {device_id}")
                raise Exception("📵 KEY đã bị gán với thiết bị khác")

        usage = df.at[idx, 'usage_count']
        try:
            usage = int(usage) if pd.notna(usage) else 0
        except Exception:
            usage = 0

        maxu = parse_int(df.at[idx, 'max_usage'])
        if maxu is not None and usage + count > maxu:
            raise Exception(f"🚫 Vượt quá số lượt cho phép ({usage + count}/{maxu})")

        df.at[idx, 'usage_count'] = usage + count
        df.to_csv(csv_file, index=False)
        print(f"✅ Đã cộng thêm {count} lượt cho KEY '{key}' (tổng: {usage + count})")

def get_key_status(key, device_id, module=None):
    """Get key status with caching"""
    info = get_key_info(key, module)
    if not info:
        return {"success": False, "message": "KEY không tồn tại"}

    ok, msg, expires, remaining = check_key_validity(key, device_id, module)
    return {
        "success": ok,
        "message": msg if not ok else "KEY hợp lệ",
        **({} if not ok else {
            "status": info['status'],
            "expires": info['expires'],
            "max_usage": info['max_usage'],
            "usage_count": info['usage_count'],
            "device_id": info['device_id'],
            "remaining": remaining,
        })
    }

def clear_key_cache():
    """Clear all key caches"""
    global _key_cache, _key_cache_timestamp
    _key_cache.clear()
    _key_cache_timestamp.clear()
