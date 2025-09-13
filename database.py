import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import threading

class DatabaseManager:
    def __init__(self, db_path: str = "keys.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""
        if not date_str:
            return None
        
        date_formats = [
            "%Y-%m-%d",           # 2025-09-30
            "%m/%d/%Y",           # 09/30/2025
            "%d/%m/%Y",           # 30/09/2025
            "%Y-%m-%d %H:%M:%S",  # 2025-09-30 12:00:00
            "%m/%d/%Y %H:%M:%S"   # 09/30/2025 12:00:00
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def get_vietnam_time(self) -> str:
        """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
        from datetime import datetime, timedelta
        utc_now = datetime.utcnow()
        vietnam_time = utc_now + timedelta(hours=7)  # UTC+7
        return vietnam_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def init_database(self):
        """Khởi tạo database và tạo bảng nếu chưa tồn tại"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tạo bảng keys
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    device_id TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    expires DATE,
                    max_usage INTEGER,
                    usage_count INTEGER DEFAULT 0,
                    module TEXT NOT NULL,
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tạo bảng activity_log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    key_value TEXT,
                    module TEXT,
                    old_values TEXT,
                    new_values TEXT,
                    user_ip TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tạo bảng api_usage_log để track end user usage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_value TEXT NOT NULL,
                    module TEXT NOT NULL,
                    device_id TEXT,
                    endpoint TEXT,
                    user_ip TEXT,
                    user_agent TEXT,
                    request_data TEXT,
                    response_status INTEGER,
                    response_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tạo bảng admin_users để quản lý admin accounts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tạo index để tăng tốc độ truy vấn
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_key ON keys(key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_id ON keys(device_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_module ON keys(module)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON keys(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_log(action)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_created_at ON activity_log(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_key ON activity_log(key_value)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_key ON api_usage_log(key_value)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_module ON api_usage_log(module)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage_log(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_ip ON api_usage_log(user_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_username ON admin_users(username)')
            
            conn.commit()
            conn.close()
    
    def get_connection(self):
        """Lấy connection đến database"""
        return sqlite3.connect(self.db_path)
    
    def get_key_info(self, key: str, module: str = None) -> Optional[Dict]:
        """Lấy thông tin key"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if module:
                cursor.execute('''
                    SELECT key, device_id, status, expires, max_usage, usage_count, module, note
                    FROM keys WHERE key = ? AND module = ?
                ''', (key, module))
            else:
                cursor.execute('''
                    SELECT key, device_id, status, expires, max_usage, usage_count, module, note
                    FROM keys WHERE key = ?
                ''', (key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'key': row[0],
                    'device_id': row[1],
                    'status': row[2],
                    'expires': row[3],
                    'max_usage': row[4],
                    'usage_count': row[5],
                    'module': row[6],
                    'note': row[7]
                }
            return None
    
    def check_key_validity(self, key: str, device_id: str, module: str = None) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Kiểm tra tính hợp lệ của key"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Kiểm tra nếu device_id đã gán cho key khác
            if module:
                cursor.execute('''
                    SELECT key FROM keys 
                    WHERE device_id = ? AND key != ? AND module = ?
                ''', (device_id, key, module))
            else:
                cursor.execute('''
                    SELECT key FROM keys 
                    WHERE device_id = ? AND key != ?
                ''', (device_id, key))
            
            existing_key = cursor.fetchone()
            if existing_key:
                conn.close()
                return False, f"❌ Thiết bị này đã được dùng với KEY khác ({existing_key[0]})!", None, None
            
            # Lấy thông tin key
            if module:
                cursor.execute('''
                    SELECT device_id, status, expires, max_usage, usage_count
                    FROM keys WHERE key = ? AND module = ?
                ''', (key, module))
            else:
                cursor.execute('''
                    SELECT device_id, status, expires, max_usage, usage_count
                    FROM keys WHERE key = ?
                ''', (key,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "❌ KEY không tồn tại!", None, None
            
            current_device, status, expires, max_usage, usage_count = row
            
            # Kiểm tra trạng thái
            if status.lower() != "active":
                conn.close()
                return False, "🔒 KEY bị khóa", None, None
            
            # Kiểm tra hạn dùng
            if not expires:
                conn.close()
                return False, "❌ KEY không có hạn sử dụng", None, None
            
            try:
                expires_date = self.parse_date(expires)
                
                if expires_date is None:
                    conn.close()
                    return False, "❌ Định dạng ngày hết hạn không hợp lệ", None, None
                
                if expires_date < datetime.now():
                    conn.close()
                    return False, "⏳ KEY đã hết hạn sử dụng", expires, None
            except Exception as e:
                conn.close()
                return False, f"❌ Lỗi xử lý ngày hết hạn: {str(e)}", None, None
            
            # Device ID ràng buộc
            if not current_device:
                # Gán device_id mới
                cursor.execute('''
                    UPDATE keys SET device_id = ?, updated_at = ?
                    WHERE key = ? AND module = ?
                ''', (device_id, self.get_vietnam_time(), key, module))
                conn.commit()
            elif current_device != device_id:
                conn.close()
                return False, "📵 KEY đã bị gán với thiết bị khác!", expires, None
            
            # Kiểm tra số lượt sử dụng
            remaining = "unlimited"
            if max_usage is not None and usage_count is not None:
                if usage_count >= max_usage:
                    conn.close()
                    return False, f"🚫 Đã dùng hết lượt ({usage_count}/{max_usage})", expires, 0
                remaining = max_usage - usage_count
            
            conn.close()
            return True, "OK", expires, remaining
    
    def update_usage_count(self, key: str, device_id: str = None, module: str = None, count: int = 1):
        """Cập nhật số lượt sử dụng"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Lấy thông tin key hiện tại
            if module:
                cursor.execute('''
                    SELECT device_id, max_usage, usage_count
                    FROM keys WHERE key = ? AND module = ?
                ''', (key, module))
            else:
                cursor.execute('''
                    SELECT device_id, max_usage, usage_count
                    FROM keys WHERE key = ?
                ''', (key,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise Exception("Key không tồn tại")
            
            current_device, max_usage, current_usage = row
            
            # Kiểm tra device_id
            if device_id:
                if not current_device:
                    cursor.execute('''
                        UPDATE keys SET device_id = ?, updated_at = ?
                        WHERE key = ? AND module = ?
                    ''', (device_id, self.get_vietnam_time(), key, module))
                elif current_device != device_id:
                    conn.close()
                    raise Exception("📵 KEY đã bị gán với thiết bị khác")
            
            # Kiểm tra số lượt sử dụng
            new_usage = (current_usage or 0) + count
            if max_usage is not None and new_usage > max_usage:
                conn.close()
                raise Exception(f"🚫 Vượt quá số lượt cho phép ({new_usage}/{max_usage})")
            
            # Cập nhật usage_count
            cursor.execute('''
                UPDATE keys SET usage_count = ?, updated_at = ?
                WHERE key = ? AND module = ?
            ''', (new_usage, self.get_vietnam_time(), key, module))
            
            conn.commit()
            conn.close()
            
            if count > 1:
                print(f"✅ Đã cộng thêm {count} lượt cho KEY '{key}' (tổng: {new_usage})")
    
    def get_key_status(self, key: str, device_id: str, module: str = None) -> Dict:
        """Lấy trạng thái key"""
        info = self.get_key_info(key, module)
        if not info:
            return {"error": "Key không tồn tại"}
        
        return {
            "key": info["key"],
            "device_id": info["device_id"],
            "status": info["status"],
            "expires": info["expires"],
            "max_usage": info["max_usage"],
            "usage_count": info["usage_count"],
            "note": info["note"],
            "remaining": "unlimited" if not info["max_usage"] else max(0, info["max_usage"] - info["usage_count"])
        }
    
    def add_key(self, key: str, module: str, device_id: str = None, 
                status: str = "active", expires: str = None, 
                max_usage: int = None, usage_count: int = 0, note: str = ""):
        """Thêm key mới"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO keys (key, device_id, status, expires, max_usage, usage_count, module, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (key, device_id, status, expires, max_usage, usage_count, module, note, self.get_vietnam_time(), self.get_vietnam_time()))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Key đã tồn tại
            finally:
                conn.close()
    
    def update_key(self, key: str, module: str, **kwargs):
        """Cập nhật thông tin key"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Xây dựng câu lệnh UPDATE động
            set_clauses = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['device_id', 'status', 'expires', 'max_usage', 'usage_count', 'note']:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                conn.close()
                return False
            
            set_clauses.append("updated_at = ?")
            values.append(self.get_vietnam_time())
            values.extend([key, module])
            
            query = f"UPDATE keys SET {', '.join(set_clauses)} WHERE key = ? AND module = ?"
            cursor.execute(query, values)
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected_rows > 0
    
    def delete_key(self, key: str, module: str):
        """Xóa key"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM keys WHERE key = ? AND module = ?', (key, module))
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            return affected_rows > 0
    
    def get_all_keys(self, module: str = None) -> List[Dict]:
        """Lấy tất cả keys"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if module:
                cursor.execute('''
                    SELECT key, device_id, status, expires, max_usage, usage_count, module, note, created_at, updated_at
                    FROM keys WHERE module = ?
                    ORDER BY created_at DESC
                ''', (module,))
            else:
                cursor.execute('''
                    SELECT key, device_id, status, expires, max_usage, usage_count, module, note, created_at, updated_at
                    FROM keys
                    ORDER BY created_at DESC
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'key': row[0],
                    'device_id': row[1],
                    'status': row[2],
                    'expires': row[3],
                    'max_usage': row[4],
                    'usage_count': row[5],
                    'module': row[6],
                    'note': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
                for row in rows
            ]
    
    def log_activity(self, action: str, key_value: str = None, module: str = None, 
                    old_values: Dict = None, new_values: Dict = None, 
                    user_ip: str = None, user_agent: str = None):
        """Ghi log hoạt động"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO activity_log (action, key_value, module, old_values, new_values, user_ip, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                action,
                key_value,
                module,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                user_ip,
                user_agent,
                self.get_vietnam_time()
            ))
            
            conn.commit()
            conn.close()
    
    def get_activity_log(self, limit: int = 50, offset: int = 0, 
                        action: str = None, module: str = None) -> List[Dict]:
        """Lấy danh sách activity log"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, action, key_value, module, old_values, new_values, user_ip, user_agent, created_at
                FROM activity_log
            '''
            params = []
            conditions = []
            
            if action:
                conditions.append('action = ?')
                params.append(action)
            
            if module:
                conditions.append('module = ?')
                params.append(module)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'action': row[1],
                    'key_value': row[2],
                    'module': row[3],
                    'old_values': json.loads(row[4]) if row[4] else None,
                    'new_values': json.loads(row[5]) if row[5] else None,
                    'user_ip': row[6],
                    'user_agent': row[7],
                    'created_at': row[8]
                }
                for row in rows
            ]
    
    def get_activity_stats(self) -> Dict:
        """Lấy thống kê activity"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tổng số hoạt động
            cursor.execute('SELECT COUNT(*) FROM activity_log')
            total_activities = cursor.fetchone()[0]
            
            # Hoạt động theo loại
            cursor.execute('''
                SELECT action, COUNT(*) 
                FROM activity_log 
                GROUP BY action 
                ORDER BY COUNT(*) DESC
            ''')
            actions = dict(cursor.fetchall())
            
            # Hoạt động theo module
            cursor.execute('''
                SELECT module, COUNT(*) 
                FROM activity_log 
                WHERE module IS NOT NULL
                GROUP BY module 
                ORDER BY COUNT(*) DESC
            ''')
            modules = dict(cursor.fetchall())
            
            # Hoạt động gần đây (24h)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM activity_log 
                WHERE created_at >= datetime('now', '-1 day')
            ''')
            recent_24h = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_activities': total_activities,
                'actions': actions,
                'modules': modules,
                'recent_24h': recent_24h
            }
    
    def log_api_usage(self, key_value: str, module: str, device_id: str = None,
                     endpoint: str = None, user_ip: str = None, user_agent: str = None,
                     request_data: Dict = None, response_status: int = None, 
                     response_message: str = None):
        """Ghi log sử dụng API của end user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_usage_log (key_value, module, device_id, endpoint, user_ip, user_agent, 
                                         request_data, response_status, response_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key_value,
                module,
                device_id,
                endpoint,
                user_ip,
                user_agent,
                json.dumps(request_data) if request_data else None,
                response_status,
                response_message,
                self.get_vietnam_time()
            ))
            
            conn.commit()
            conn.close()
    
    def get_api_usage_log(self, limit: int = 50, offset: int = 0,
                         key_value: str = None, module: str = None,
                         user_ip: str = None, endpoint: str = None) -> List[Dict]:
        """Lấy danh sách API usage log"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = '''
                SELECT id, key_value, module, device_id, endpoint, user_ip, user_agent, 
                       request_data, response_status, response_message, created_at
                FROM api_usage_log
            '''
            params = []
            conditions = []
            
            if key_value:
                conditions.append('key_value = ?')
                params.append(key_value)
            
            if module:
                conditions.append('module = ?')
                params.append(module)
            
            if user_ip:
                conditions.append('user_ip = ?')
                params.append(user_ip)
            
            if endpoint:
                conditions.append('endpoint = ?')
                params.append(endpoint)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'key_value': row[1],
                    'module': row[2],
                    'device_id': row[3],
                    'endpoint': row[4],
                    'user_ip': row[5],
                    'user_agent': row[6],
                    'request_data': json.loads(row[7]) if row[7] else None,
                    'response_status': row[8],
                    'response_message': row[9],
                    'created_at': row[10]
                }
                for row in rows
            ]
    
    def get_api_usage_stats(self) -> Dict:
        """Lấy thống kê API usage"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tổng số API calls
            cursor.execute('SELECT COUNT(*) FROM api_usage_log')
            total_calls = cursor.fetchone()[0]
            
            # API calls theo module
            cursor.execute('''
                SELECT module, COUNT(*) 
                FROM api_usage_log 
                GROUP BY module 
                ORDER BY COUNT(*) DESC
            ''')
            modules = dict(cursor.fetchall())
            
            # API calls theo endpoint
            cursor.execute('''
                SELECT endpoint, COUNT(*) 
                FROM api_usage_log 
                WHERE endpoint IS NOT NULL
                GROUP BY endpoint 
                ORDER BY COUNT(*) DESC
            ''')
            endpoints = dict(cursor.fetchall())
            
            # API calls theo IP
            cursor.execute('''
                SELECT user_ip, COUNT(*) 
                FROM api_usage_log 
                WHERE user_ip IS NOT NULL
                GROUP BY user_ip 
                ORDER BY COUNT(*) DESC
                LIMIT 10
            ''')
            top_ips = dict(cursor.fetchall())
            
            # API calls gần đây (24h)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM api_usage_log 
                WHERE created_at >= datetime('now', '-1 day')
            ''')
            recent_24h = cursor.fetchone()[0]
            
            # Response status stats
            cursor.execute('''
                SELECT response_status, COUNT(*) 
                FROM api_usage_log 
                WHERE response_status IS NOT NULL
                GROUP BY response_status 
                ORDER BY COUNT(*) DESC
            ''')
            status_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_calls': total_calls,
                'modules': modules,
                'endpoints': endpoints,
                'top_ips': top_ips,
                'recent_24h': recent_24h,
                'status_stats': status_stats
            }
    
    def create_admin_user(self, username: str, password: str, email: str = None) -> bool:
        """Tạo admin user mới"""
        import hashlib
        
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            try:
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                cursor.execute('''
                    INSERT INTO admin_users (username, password_hash, email)
                    VALUES (?, ?, ?)
                ''', (username, password_hash, email))
                
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False  # Username đã tồn tại
            finally:
                conn.close()
    
    def verify_admin_user(self, username: str, password: str) -> Optional[Dict]:
        """Xác thực admin user"""
        import hashlib
        
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                SELECT id, username, email, is_active, last_login
                FROM admin_users 
                WHERE username = ? AND password_hash = ? AND is_active = 1
            ''', (username, password_hash))
            
            row = cursor.fetchone()
            if row:
                # Cập nhật last_login
                cursor.execute('''
                    UPDATE admin_users 
                    SET last_login = ?
                    WHERE id = ?
                ''', (self.get_vietnam_time(), row[0]))
                conn.commit()
                
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'is_active': row[3],
                    'last_login': row[4]
                }
            
            conn.close()
            return None
    
    def get_admin_user(self, username: str) -> Optional[Dict]:
        """Lấy thông tin admin user"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, is_active, last_login, created_at
                FROM admin_users WHERE username = ?
            ''', (username,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'is_active': row[3],
                    'last_login': row[4],
                    'created_at': row[5]
                }
            return None

# Tạo instance global
db_manager = DatabaseManager()