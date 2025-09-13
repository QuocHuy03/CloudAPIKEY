from functools import wraps
from flask import request, jsonify, session, redirect, url_for, flash

def require_admin_login(f):
    """Decorator yêu cầu đăng nhập admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            if request.is_json:
                return jsonify(success=False, message="🔒 Yêu cầu đăng nhập"), 401
            else:
                flash('Vui lòng đăng nhập để truy cập trang admin', 'warning')
                return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_login_required(f):
    """Decorator cho API endpoints yêu cầu đăng nhập admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return jsonify(success=False, message="🔒 Yêu cầu đăng nhập admin"), 401
        return f(*args, **kwargs)
    return decorated_function