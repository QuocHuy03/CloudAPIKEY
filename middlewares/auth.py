from functools import wraps
from flask import request, jsonify
from services.key_service_wrapper import check_key_validity
from database import db_manager
import json

def require_auth(module=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == "GET":
                key = request.args.get("key", "").strip()
                device_id = request.args.get("device_id", "").strip()
            else:
                key = request.form.get("key", "").strip()
                device_id = request.form.get("device_id", "").strip()

            # ✅ In log sau khi đã lấy xong biến
            print(f"[DEBUG] Method: {request.method}")
            print(f"[DEBUG] key: {key}")
            print(f"[DEBUG] device_id: {device_id}")

            if not key or not device_id:
                # Log failed attempt
                try:
                    db_manager.log_api_usage(
                        key_value=key or "unknown",
                        module=module or "unknown",
                        device_id=device_id or "unknown",
                        endpoint=request.endpoint,
                        user_ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent'),
                        request_data=dict(request.form) if request.form else dict(request.args),
                        response_status=400,
                        response_message="Missing key or device_id"
                    )
                except Exception as e:
                    print(f"Error logging API usage: {e}")
                
                return jsonify(success=False, message="🔒 Thiếu trường key hoặc device_id"), 400

            is_valid, msg, expires, remaining = check_key_validity(key, device_id, module=module)
            if not is_valid:
                # Log failed validation
                try:
                    db_manager.log_api_usage(
                        key_value=key,
                        module=module or "unknown",
                        device_id=device_id,
                        endpoint=request.endpoint,
                        user_ip=request.remote_addr,
                        user_agent=request.headers.get('User-Agent'),
                        request_data=dict(request.form) if request.form else dict(request.args),
                        response_status=403,
                        response_message=msg
                    )
                except Exception as e:
                    print(f"Error logging API usage: {e}")
                
                return jsonify(success=False, message=msg), 403

            # Log successful validation
            try:
                db_manager.log_api_usage(
                    key_value=key,
                    module=module or "unknown",
                    device_id=device_id,
                    endpoint=request.endpoint,
                    user_ip=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_data=dict(request.form) if request.form else dict(request.args),
                    response_status=200,
                    response_message="Authentication successful"
                )
            except Exception as e:
                print(f"Error logging API usage: {e}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator
