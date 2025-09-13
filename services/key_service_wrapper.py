"""
Key Service Wrapper - Cho phép chuyển đổi giữa CSV và SQL database
"""

from config import USE_SQL_DATABASE

if USE_SQL_DATABASE:
    # Import SQL-based service
    from .key_service_sql import *
    print("✅ Sử dụng SQL Database cho Key Management")
else:
    # Import CSV-based service (backward compatibility)
    from .key_service_wrapper import *
    print("⚠️  Sử dụng CSV files cho Key Management (deprecated)")

# Export tất cả functions để maintain compatibility
__all__ = [
    'get_key_info',
    'check_key_validity', 
    'update_usage_count',
    'update_usage_count_by',
    'get_key_status',
    'parse_int',
    'parse_date',
    'get_csv_file'  # Deprecated but kept for compatibility
]

# Thêm các functions mới chỉ có trong SQL version
if USE_SQL_DATABASE:
    __all__.extend([
        'add_key',
        'update_key', 
        'delete_key',
        'get_all_keys',
        'get_keys_by_status',
        'get_expired_keys',
        'get_keys_by_device',
        'get_usage_statistics'
    ])