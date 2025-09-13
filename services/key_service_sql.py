"""
Key Service sử dụng SQL Database thay vì CSV
"""

from database import db_manager
from datetime import datetime
from typing import Optional, Dict, Tuple

def parse_int(i):
    """Parse integer với error handling"""
    try:
        return int(i)
    except:
        return None

def parse_date(d):
    """Parse date với multiple format support"""
    if not d:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(str(d), fmt)
        except ValueError:
            continue
    return None

def get_key_info(key: str, module: str = None) -> Optional[Dict]:
    """Lấy thông tin key từ database"""
    return db_manager.get_key_info(key, module)

def check_key_validity(key: str, device_id: str, module: str = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """Kiểm tra tính hợp lệ của key"""
    return db_manager.check_key_validity(key, device_id, module)

def update_usage_count(key: str, device_id: str = None, module: str = None):
    """Cập nhật số lượt sử dụng (tăng 1)"""
    db_manager.update_usage_count(key, device_id, module, 1)

def update_usage_count_by(key: str, count: int, device_id: str = None, module: str = None):
    """Cập nhật số lượt sử dụng (tăng theo số lượng)"""
    if not isinstance(count, int) or count <= 0:
        raise Exception("❌ Giá trị 'count' phải là số nguyên dương")
    
    db_manager.update_usage_count(key, device_id, module, count)

def get_key_status(key: str, device_id: str, module: str = None) -> Dict:
    """Lấy trạng thái key"""
    return db_manager.get_key_status(key, device_id, module)

# Các hàm tiện ích để quản lý keys
def add_key(key: str, module: str, device_id: str = None, 
            status: str = "active", expires: str = None, 
            max_usage: int = None, usage_count: int = 0) -> bool:
    """Thêm key mới"""
    return db_manager.add_key(key, module, device_id, status, expires, max_usage, usage_count)

def update_key(key: str, module: str, **kwargs) -> bool:
    """Cập nhật thông tin key"""
    return db_manager.update_key(key, module, **kwargs)

def delete_key(key: str, module: str) -> bool:
    """Xóa key"""
    return db_manager.delete_key(key, module)

def get_all_keys(module: str = None) -> list:
    """Lấy tất cả keys"""
    return db_manager.get_all_keys(module)

def get_keys_by_status(status: str, module: str = None) -> list:
    """Lấy keys theo trạng thái"""
    all_keys = db_manager.get_all_keys(module)
    return [key for key in all_keys if key['status'].lower() == status.lower()]

def get_expired_keys(module: str = None) -> list:
    """Lấy danh sách keys đã hết hạn"""
    all_keys = db_manager.get_all_keys(module)
    expired_keys = []
    
    for key in all_keys:
        if key['expires']:
            try:
                expires_date = datetime.strptime(key['expires'], "%m/%d/%Y")
                if expires_date < datetime.now():
                    expired_keys.append(key)
            except ValueError:
                continue
    
    return expired_keys

def get_keys_by_device(device_id: str, module: str = None) -> list:
    """Lấy keys theo device_id"""
    all_keys = db_manager.get_all_keys(module)
    return [key for key in all_keys if key['device_id'] == device_id]

def get_usage_statistics(module: str = None) -> Dict:
    """Lấy thống kê sử dụng"""
    all_keys = db_manager.get_all_keys(module)
    
    total_keys = len(all_keys)
    active_keys = len([k for k in all_keys if k['status'].lower() == 'active'])
    expired_keys = len(get_expired_keys(module))
    
    total_usage = sum(k['usage_count'] or 0 for k in all_keys)
    total_max_usage = sum(k['max_usage'] or 0 for k in all_keys if k['max_usage'])
    
    return {
        'total_keys': total_keys,
        'active_keys': active_keys,
        'expired_keys': expired_keys,
        'total_usage': total_usage,
        'total_max_usage': total_max_usage,
        'usage_percentage': (total_usage / total_max_usage * 100) if total_max_usage > 0 else 0
    }

# Backward compatibility - giữ nguyên interface cũ
def get_csv_file(module=None):
    """Deprecated: Chỉ để backward compatibility"""
    print("⚠️  get_csv_file() is deprecated. Use SQL database instead.")
    return None