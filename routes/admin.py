from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from database import db_manager
from datetime import datetime
from middlewares.admin_auth import require_admin_login, admin_login_required
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Danh sách các module có sẵn
AVAILABLE_MODULES = [
    'voice',
    'image', 
    'clone_voice',
    'music',
    'make_video_ai',
    'merger_video_ai'
]

# Routes cho authentication
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập admin"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin đăng nhập!', 'error')
            return render_template('admin/login.html')
        
        # Xác thực user
        user = db_manager.verify_admin_user(username, password)
        if user:
            session['admin_logged_in'] = True
            session['admin_user'] = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
            flash(f'Chào mừng {user["username"]}! Đăng nhập thành công.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
            return render_template('admin/login.html')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Đăng xuất admin"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('Đã đăng xuất thành công!', 'info')
    return redirect(url_for('admin.login'))

def log_activity(action, key_value=None, module=None, old_values=None, new_values=None):
    """Helper function để log activity"""
    try:
        db_manager.log_activity(
            action=action,
            key_value=key_value,
            module=module,
            old_values=old_values,
            new_values=new_values,
            user_ip=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
    except Exception as e:
        print(f"Error logging activity: {e}")

@admin_bp.route('/')
@require_admin_login
def dashboard():
    """Trang chủ admin dashboard"""
    # Lấy thống kê tổng quan
    stats = {}
    for module in AVAILABLE_MODULES:
        keys = db_manager.get_all_keys(module)
        
        # Count expired keys efficiently
        expired_count = 0
        for k in keys:
            if k['expires']:
                expires_date = db_manager.parse_date(k['expires'])
                if expires_date and expires_date < datetime.now():
                    expired_count += 1
        
        stats[module] = {
            'total': len(keys),
            'active': len([k for k in keys if k['status'] == 'active']),
            'expired': expired_count,
            'used_up': len([k for k in keys if k['max_usage'] and k['usage_count'] >= k['max_usage']])
        }
    
    return render_template('admin/dashboard.html', stats=stats, modules=AVAILABLE_MODULES)

@admin_bp.route('/keys')
@require_admin_login
def keys_list():
    """Danh sách tất cả keys"""
    module = request.args.get('module', '')
    keys = db_manager.get_all_keys(module if module in AVAILABLE_MODULES else None)
    
    # Format dữ liệu cho hiển thị
    for key in keys:
        if key['expires']:
            expires_date = db_manager.parse_date(key['expires'])
            if expires_date:
                key['is_expired'] = expires_date < datetime.now()
                key['expires_formatted'] = expires_date.strftime('%d/%m/%Y')
            else:
                key['is_expired'] = False
                key['expires_formatted'] = key['expires']
        else:
            key['is_expired'] = False
            key['expires_formatted'] = 'Không giới hạn'
        
        # Tính remaining usage
        if key['max_usage']:
            key['remaining'] = max(0, key['max_usage'] - key['usage_count'])
        else:
            key['remaining'] = 'unlimited'
    
    return render_template('admin/keys_list.html', keys=keys, modules=AVAILABLE_MODULES, current_module=module)

@admin_bp.route('/keys/add', methods=['GET', 'POST'])
@require_admin_login
def add_key():
    """Thêm key mới"""
    if request.method == 'POST':
        data = request.get_json()
        
        key = (data.get('key') or '').strip()
        module = (data.get('module') or '').strip()
        device_id = (data.get('device_id') or '').strip() or None
        status = (data.get('status') or 'active').strip()
        expires = (data.get('expires') or '').strip() or None
        max_usage = data.get('max_usage')
        usage_count = data.get('usage_count', 0)
        note = (data.get('note') or '').strip()
        
        # Validation
        if not key:
            return jsonify({'success': False, 'message': 'Key không được để trống'})
        
        if module not in AVAILABLE_MODULES:
            return jsonify({'success': False, 'message': 'Module không hợp lệ'})
        
        if max_usage:
            try:
                max_usage = int(max_usage)
                if max_usage <= 0:
                    return jsonify({'success': False, 'message': 'Max usage phải là số dương'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Max usage phải là số nguyên'})
        
        if usage_count:
            try:
                usage_count = int(usage_count)
                if usage_count < 0:
                    return jsonify({'success': False, 'message': 'Usage count không được âm'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Usage count phải là số nguyên'})
        
        # Thêm key vào database
        success = db_manager.add_key(
            key=key,
            module=module,
            device_id=device_id,
            status=status,
            expires=expires,
            max_usage=max_usage,
            usage_count=usage_count,
            note=note
        )
        
        if success:
            # Log activity
            log_activity(
                action='CREATE_KEY',
                key_value=key,
                module=module,
                new_values={
                    'key': key,
                    'module': module,
                    'device_id': device_id,
                    'status': status,
                    'expires': expires,
                    'max_usage': max_usage,
                    'usage_count': usage_count
                }
            )
            return jsonify({'success': True, 'message': 'Thêm key thành công'})
        else:
            return jsonify({'success': False, 'message': 'Key đã tồn tại'})
    
    return render_template('admin/add_key.html', modules=AVAILABLE_MODULES)

@admin_bp.route('/keys/<module>/<key>/edit', methods=['GET', 'POST'])
@require_admin_login
def edit_key(module, key):
    """Chỉnh sửa key"""
    if module not in AVAILABLE_MODULES:
        return jsonify({'success': False, 'message': 'Module không hợp lệ'})
    
    if request.method == 'POST':
        data = request.get_json()
        
        device_id = (data.get('device_id') or '').strip() or None
        status = (data.get('status') or 'active').strip()
        expires = (data.get('expires') or '').strip() or None
        max_usage = data.get('max_usage')
        usage_count = data.get('usage_count', 0)
        note = (data.get('note') or '').strip() or None
        
        # Validation
        if max_usage:
            try:
                max_usage = int(max_usage)
                if max_usage <= 0:
                    return jsonify({'success': False, 'message': 'Max usage phải là số dương'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Max usage phải là số nguyên'})
        
        if usage_count:
            try:
                usage_count = int(usage_count)
                if usage_count < 0:
                    return jsonify({'success': False, 'message': 'Usage count không được âm'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Usage count phải là số nguyên'})
        
        # Cập nhật key
        success = db_manager.update_key(
            key=key,
            module=module,
            device_id=device_id,
            status=status,
            expires=expires,
            max_usage=max_usage,
            usage_count=usage_count,
            note=note
        )
        
        if success:
            # Log activity
            log_activity(
                action='UPDATE_KEY',
                key_value=key,
                module=module,
                old_values=db_manager.get_key_info(key, module),
                new_values={
                    'device_id': device_id,
                    'status': status,
                    'expires': expires,
                    'max_usage': max_usage,
                    'usage_count': usage_count,
                    'note': note
                }
            )
            return jsonify({'success': True, 'message': 'Cập nhật key thành công'})
        else:
            return jsonify({'success': False, 'message': 'Không thể cập nhật key'})
    
    # Lấy thông tin key hiện tại
    key_info = db_manager.get_key_info(key, module)
    if not key_info:
        return jsonify({'success': False, 'message': 'Key không tồn tại'})
    
    return render_template('admin/edit_key.html', key_info=key_info, modules=AVAILABLE_MODULES)

@admin_bp.route('/keys/<module>/<key>/delete', methods=['POST'])
@require_admin_login
def delete_key(module, key):
    """Xóa key"""
    if module not in AVAILABLE_MODULES:
        return jsonify({'success': False, 'message': 'Module không hợp lệ'})
    
    # Lấy thông tin key trước khi xóa để log
    key_info = db_manager.get_key_info(key, module)
    
    success = db_manager.delete_key(key, module)
    
    if success:
        # Log activity
        log_activity(
            action='DELETE_KEY',
            key_value=key,
            module=module,
            old_values=key_info
        )
        return jsonify({'success': True, 'message': 'Xóa key thành công'})
    else:
        return jsonify({'success': False, 'message': 'Không thể xóa key'})

@admin_bp.route('/keys/<module>/<key>/status')
@require_admin_login
def key_status(module, key):
    """Xem trạng thái chi tiết của key"""
    if module not in AVAILABLE_MODULES:
        return jsonify({'success': False, 'message': 'Module không hợp lệ'})
    
    key_info = db_manager.get_key_info(key, module)
    if not key_info:
        return jsonify({'success': False, 'message': 'Key không tồn tại'})
    
    # Tính toán thông tin bổ sung
    if key_info['expires']:
        try:
            expires_date = db_manager.parse_date(key_info['expires'])
            if expires_date:
                key_info['is_expired'] = expires_date < datetime.now()
                key_info['expires_formatted'] = expires_date.strftime('%d/%m/%Y')
            else:
                key_info['is_expired'] = False
                key_info['expires_formatted'] = key_info['expires']
        except:
            key_info['is_expired'] = False
            key_info['expires_formatted'] = key_info['expires']
    else:
        key_info['is_expired'] = False
        key_info['expires_formatted'] = 'Không giới hạn'
    
    # Tính remaining usage
    if key_info['max_usage']:
        key_info['remaining'] = max(0, key_info['max_usage'] - key_info['usage_count'])
    else:
        key_info['remaining'] = 'unlimited'
    
    return render_template('admin/key_status.html', key_info=key_info)

@admin_bp.route('/api/keys')
@admin_login_required
def api_keys():
    """API endpoint để lấy danh sách keys (cho AJAX)"""
    module = request.args.get('module', '')
    keys = db_manager.get_all_keys(module if module in AVAILABLE_MODULES else None)
    
    # Format dữ liệu
    for key in keys:
        if key['expires']:
            expires_date = db_manager.parse_date(key['expires'])
            if expires_date:
                key['is_expired'] = expires_date < datetime.now()
            else:
                key['is_expired'] = False
        else:
            key['is_expired'] = False
        
        if key['max_usage']:
            key['remaining'] = max(0, key['max_usage'] - key['usage_count'])
        else:
            key['remaining'] = 'unlimited'
    
    return jsonify({'success': True, 'data': keys})

@admin_bp.route('/api/stats')
@admin_login_required
def api_stats():
    """API endpoint để lấy thống kê"""
    stats = {}
    for module in AVAILABLE_MODULES:
        keys = db_manager.get_all_keys(module)
        # Count expired keys efficiently
        expired_count = 0
        for k in keys:
            if k['expires']:
                expires_date = db_manager.parse_date(k['expires'])
                if expires_date and expires_date < datetime.now():
                    expired_count += 1
        
        stats[module] = {
            'total': len(keys),
            'active': len([k for k in keys if k['status'] == 'active']),
            'expired': expired_count,
            'used_up': len([k for k in keys if k['max_usage'] and k['usage_count'] >= k['max_usage']])
        }
    
    return jsonify({'success': True, 'data': stats})

@admin_bp.route('/activity')
@require_admin_login
def activity_log():
    """Trang hiển thị activity log"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    module_filter = request.args.get('module', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    activities = db_manager.get_activity_log(
        limit=limit,
        offset=offset,
        action=action_filter if action_filter else None,
        module=module_filter if module_filter else None
    )
    
    # Lấy thống kê activity
    activity_stats = db_manager.get_activity_stats()
    
    return render_template('admin/activity_log.html', 
                         activities=activities,
                         activity_stats=activity_stats,
                         current_page=page,
                         action_filter=action_filter,
                         module_filter=module_filter,
                         modules=AVAILABLE_MODULES)

@admin_bp.route('/usage-history')
@require_admin_login
def usage_history():
    """Trang hiển thị lịch sử sử dụng API"""
    page = request.args.get('page', 1, type=int)
    key_filter = request.args.get('key', '')
    module_filter = request.args.get('module', '')
    endpoint_filter = request.args.get('endpoint', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    usage_logs = db_manager.get_api_usage_log(
        limit=limit,
        offset=offset,
        key_value=key_filter if key_filter else None,
        module=module_filter if module_filter else None,
        endpoint=endpoint_filter if endpoint_filter else None
    )
    
    # Lấy thống kê usage
    usage_stats = db_manager.get_api_usage_stats()
    
    return render_template('admin/usage_history.html', 
                         usage_logs=usage_logs,
                         usage_stats=usage_stats,
                         current_page=page,
                         key_filter=key_filter,
                         module_filter=module_filter,
                         endpoint_filter=endpoint_filter,
                         modules=AVAILABLE_MODULES)

@admin_bp.route('/api/usage-history')
@admin_login_required
def api_usage_history():
    """API endpoint để lấy usage history"""
    page = request.args.get('page', 1, type=int)
    key_filter = request.args.get('key', '')
    module_filter = request.args.get('module', '')
    endpoint_filter = request.args.get('endpoint', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    usage_logs = db_manager.get_api_usage_log(
        limit=limit,
        offset=offset,
        key_value=key_filter if key_filter else None,
        module=module_filter if module_filter else None,
        endpoint=endpoint_filter if endpoint_filter else None
    )
    
    return jsonify({
        'success': True,
        'data': usage_logs,
        'page': page,
        'has_more': len(usage_logs) == limit
    })

@admin_bp.route('/api/combined-activity')
@admin_login_required
def api_combined_activity():
    """API endpoint để lấy cả activity log và API usage log gộp lại"""
    limit = request.args.get('limit', 20, type=int)
    
    # Lấy activity log
    activities = db_manager.get_activity_log(
        limit=limit,
        offset=0,
        action=None,
        module=None
    )
    
    # Lấy API usage log
    usage_logs = db_manager.get_api_usage_log(
        limit=limit,
        offset=0,
        key_value=None,
        module=None,
        user_ip=None,
        endpoint=None
    )
    
    # Gộp và sắp xếp theo thời gian
    combined_logs = []
    
    # Thêm activity logs với type indicator
    for activity in activities:
        combined_logs.append({
            'id': f"activity_{activity['id']}",
            'type': 'activity',
            'created_at': activity['created_at'],
            'action': activity['action'],
            'key_value': activity['key_value'],
            'module': activity['module'],
            'user_ip': activity['user_ip'],
            'user_agent': activity['user_agent'],
            'old_values': activity['old_values'],
            'new_values': activity['new_values'],
            'response_status': None,
            'response_message': None,
            'endpoint': None,
            'device_id': None
        })
    
    # Thêm API usage logs với type indicator
    for usage in usage_logs:
        combined_logs.append({
            'id': f"usage_{usage['id']}",
            'type': 'api_usage',
            'created_at': usage['created_at'],
            'action': f"API_{usage['endpoint']}" if usage['endpoint'] else 'API_CALL',
            'key_value': usage['key_value'],
            'module': usage['module'],
            'user_ip': usage['user_ip'],
            'user_agent': usage['user_agent'],
            'old_values': None,
            'new_values': None,
            'response_status': usage['response_status'],
            'response_message': usage['response_message'],
            'endpoint': usage['endpoint'],
            'device_id': usage['device_id']
        })
    
    # Sắp xếp theo thời gian giảm dần (mới nhất trước)
    combined_logs.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Giới hạn số lượng
    combined_logs = combined_logs[:limit]
    
    return jsonify({'success': True, 'data': combined_logs})

@admin_bp.route('/api/activity')
@admin_login_required
def api_activity():
    """API endpoint để lấy activity log"""
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    module_filter = request.args.get('module', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    activities = db_manager.get_activity_log(
        limit=limit,
        offset=offset,
        action=action_filter if action_filter else None,
        module=module_filter if module_filter else None
    )
    
    return jsonify({'success': True, 'data': activities})

@admin_bp.route('/api/activity/stats')
@admin_login_required
def api_activity_stats():
    """API endpoint để lấy thống kê activity"""
    stats = db_manager.get_activity_stats()
    return jsonify({'success': True, 'data': stats})

@admin_bp.route('/api/activity/cleanup', methods=['POST'])
@admin_login_required
def api_activity_cleanup():
    """API endpoint để làm sạch activity log"""
    try:
        data = request.get_json()
        
        # Lấy các tham số từ request
        days_to_keep = data.get('days_to_keep', None)
        action_filter = data.get('action_filter', None)
        module_filter = data.get('module_filter', None)
        
        # Validate parameters
        if days_to_keep is not None:
            try:
                days_to_keep = int(days_to_keep)
                if days_to_keep < 0:
                    return jsonify({'success': False, 'message': 'Số ngày phải >= 0'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Số ngày không hợp lệ'})
        
        # Thực hiện cleanup
        result = db_manager.clean_activity_log(
            days_to_keep=days_to_keep,
            action_filter=action_filter,
            module_filter=module_filter
        )
        
        # Log activity về việc cleanup
        log_activity(
            action='CLEANUP_ACTIVITY_LOG',
            old_values={
                'days_to_keep': days_to_keep,
                'action_filter': action_filter,
                'module_filter': module_filter,
                'deleted_count': result['deleted_count']
            }
        )
        
        return jsonify({
            'success': True, 
            'message': f'Đã xóa {result["deleted_count"]} records. Còn lại {result["remaining_count"]} records.',
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi khi làm sạch: {str(e)}'})

@admin_bp.route('/api-usage')
@require_admin_login
def api_usage_log():
    """Trang hiển thị API usage log của end users"""
    page = request.args.get('page', 1, type=int)
    key_filter = request.args.get('key', '')
    module_filter = request.args.get('module', '')
    ip_filter = request.args.get('ip', '')
    endpoint_filter = request.args.get('endpoint', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    usage_logs = db_manager.get_api_usage_log(
        limit=limit,
        offset=offset,
        key_value=key_filter if key_filter else None,
        module=module_filter if module_filter else None,
        user_ip=ip_filter if ip_filter else None,
        endpoint=endpoint_filter if endpoint_filter else None
    )
    
    # Lấy thống kê API usage
    usage_stats = db_manager.get_api_usage_stats()
    
    return render_template('admin/api_usage_log.html', 
                         usage_logs=usage_logs,
                         usage_stats=usage_stats,
                         current_page=page,
                         key_filter=key_filter,
                         module_filter=module_filter,
                         ip_filter=ip_filter,
                         endpoint_filter=endpoint_filter,
                         modules=AVAILABLE_MODULES)

@admin_bp.route('/api/api-usage')
@admin_login_required
def api_api_usage():
    """API endpoint để lấy API usage log"""
    page = request.args.get('page', 1, type=int)
    key_filter = request.args.get('key', '')
    module_filter = request.args.get('module', '')
    ip_filter = request.args.get('ip', '')
    endpoint_filter = request.args.get('endpoint', '')
    
    limit = 20
    offset = (page - 1) * limit
    
    usage_logs = db_manager.get_api_usage_log(
        limit=limit,
        offset=offset,
        key_value=key_filter if key_filter else None,
        module=module_filter if module_filter else None,
        user_ip=ip_filter if ip_filter else None,
        endpoint=endpoint_filter if endpoint_filter else None
    )
    
    return jsonify({'success': True, 'data': usage_logs})

@admin_bp.route('/api/api-usage/stats')
@admin_login_required
def api_api_usage_stats():
    """API endpoint để lấy thống kê API usage"""
    stats = db_manager.get_api_usage_stats()
    return jsonify({'success': True, 'data': stats})

@admin_bp.route('/keys/export-excel')
@admin_login_required
def export_keys_excel():
    """Xuất danh sách keys ra file Excel"""
    try:
        import pandas as pd
        from io import BytesIO
        from flask import make_response
        
        # Lấy tất cả keys
        keys = db_manager.get_all_keys()
        
        # Tạo DataFrame
        data = []
        for key in keys:
            data.append({
                'STT': len(data) + 1,
                'Key': key['key'],
                'Module': key['module'],
                'Device ID': key['device_id'] or 'Chưa gán',
                'Trạng thái': 'Active' if key['status'] == 'active' else 'Inactive',
                'Hết hạn': key['expires'] or 'Không giới hạn',
                'Sử dụng': f"{key['usage_count']}/{key['max_usage']}" if key['max_usage'] else f"{key['usage_count']} (unlimited)",
                'Còn lại': 'Unlimited' if not key['max_usage'] else max(0, key['max_usage'] - key['usage_count']),
                'Ghi chú': key['note'] or 'Không có ghi chú',
                'Ngày tạo': key['created_at'],
                'Ngày cập nhật': key['updated_at']
            })
        
        df = pd.DataFrame(data)
        
        # Tạo file Excel trong memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Danh sách Keys', index=False)
        
        output.seek(0)
        
        # Tạo response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=keys_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except ImportError:
        flash('Cần cài đặt pandas và openpyxl để xuất Excel!', 'error')
        return redirect(url_for('admin.keys_list'))
    except Exception as e:
        flash(f'Lỗi khi xuất Excel: {str(e)}', 'error')
        return redirect(url_for('admin.keys_list'))
        return redirect(url_for('admin.keys_list'))