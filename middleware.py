from functools import wraps
import jwt
import datetime
import logging
from logging.handlers import RotatingFileHandler
import json
import os
from flask import request, jsonify, abort

# === Настройка логгера для аудита ===
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Проверяем, существует ли уже обработчик, чтобы не дублировать
if not audit_logger.handlers:
    audit_handler = RotatingFileHandler('audit.log', maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    audit_formatter = logging.Formatter('%(levelname)s [%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)


# === Middleware для проверки прав доступа ===
def role_required(required_role='user'):
    """
    Декоратор, который проверяет, есть ли у пользователя нужная роль.
    Примеры: @role_required('admin'), @role_required('moderator')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                abort(401, description="Токен отсутствует")

            try:
                token = auth_header
                payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
                user_role = payload.get('role', 'user')

                # Проверяем, достаточно ли прав
                allowed_roles = {
                    'admin': ['admin'],
                    'moderator': ['admin', 'moderator'],
                    'user': ['admin', 'moderator', 'user']
                }

                if user_role not in allowed_roles.get(required_role, []):
                    abort(403, description=f"Нет прав: требуется роль {required_role}")

                # Логируем действие пользователя
                audit_logger.info(f"{payload['email']} ({user_role}) вызвал маршрут {request.path} | IP: {request.remote_addr}")
            except jwt.ExpiredSignatureError:
                abort(401, description="Токен истёк")
            except jwt.InvalidTokenError:
                abort(401, description="Неверный токен")

            return func(*args, **kwargs)
        return wrapper
    return decorator


# === Middleware для автоматической проверки API-ключа и логирования ===
def setup_middleware(app):
    @app.before_request
    def api_key_and_logging_middleware():
        excluded_routes = ['/api/login', '/api/register']

        if request.path in excluded_routes or request.method == 'OPTIONS':
            return None

        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API ключ отсутствует"}), 401

        if api_key not in app.config.get('ALLOWED_API_KEYS', []):
            return jsonify({"error": "Неверный API ключ"}), 403

        # Сохраняем время начала запроса
        request._start_time = datetime.datetime.now()
        return None

    @app.after_request
    def log_request_info(response):
        if hasattr(request, '_start_time'):
            elapsed = (datetime.datetime.now() - request._start_time).total_seconds() * 1000  # в мс
            logging.info(f"{request.remote_addr} {request.method} {request.path} → {response.status} за {int(elapsed)}ms")

        return response