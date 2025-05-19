from flask import Flask, jsonify, Blueprint, request, abort
from scripts import *
from flask_cors import CORS
import jwt
import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from dotenv import load_dotenv
import os
from middleware import setup_middleware, role_required

load_dotenv()

if __name__ != '__main__':
    CORS(app)
    setup_middleware(app)

VERSION = "test"

ALLOWED_API_KEYS = os.getenv("ALLOWED_API_KEYS", "").split(",")
ALLOWED_API_KEYS = [key.strip() for key in ALLOWED_API_KEYS if key.strip()]

SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ACCESS_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_EXPIRES_HOURS", "24"))
DEBUG = os.getenv("DEBUG", "False").lower() in ["true", "1"]
required_env_vars = ["SECRET_KEY", "DB_PATH"]

api = Blueprint(
    "api",
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api'
)

def check_api_key(api_key):
    if api_key not in ALLOWED_API_KEYS:
        abort(401, description="Неверный API ключ")

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            abort(401, description="API ключ отсутствует в заголовках")

        if api_key not in ALLOWED_API_KEYS:
            abort(403, description="Доступ запрещён: неверный API ключ")

        return func(*args, **kwargs)
    return wrapper

def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Токен отсутствует"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Токен истёк"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Неверный токен"}), 401

        return func(current_user_id, *args, **kwargs)
    return wrapper


# РОУТЫ
@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')  # Может быть email или телефон
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"error": "Email/телефон и пароль обязательны"}), 400

    # Поиск по email
    user = SQL_request("SELECT * FROM users WHERE email = ?", params=(identifier,), fetch='one')
    if not user and '@' not in identifier:  # Если это не email, попробуем телефон
        user = SQL_request("SELECT * FROM users WHERE phone_number = ?", params=(identifier,), fetch='one')

    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    # Проверяем пароль
    if not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Неверный пароль"}), 401

    # Обновляем last_login
    SQL_request(
        "UPDATE users SET last_login = datetime('now') WHERE user_id = ?",
        params=(user['user_id'],),
        fetch='none'
    )

    # Генерируем JWT
    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "token": token,
        "user": {
            "user_id": user['user_id'],
            "first_name": user['first_name'],
            "last_name": user['last_name'],
            "email": user['email'],
            "role": user['role'],
            "balance": user['balance']
        }
    }), 200


@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['first_name', 'last_name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Поле '{field}' обязательно"}), 400

    email = data['email'].strip().lower()
    password = data['password']

    # Проверяем, существует ли пользователь
    existing_user = SQL_request(
        "SELECT user_id FROM users WHERE email = ?",
        params=(email,),
        fetch='one'
    )
    if existing_user:
        return jsonify({"error": "Пользователь с таким email уже существует"}), 400

    # Хэшируем пароль
    hashed_password = generate_password_hash(password)

    # Подготавливаем данные
    try:
        SQL_request(
            """INSERT INTO users (
                first_name, middle_name, last_name, email, phone_number,
                password_hash, date_of_birth, gender, created_at, cart, inventory
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), '{}', '{}')""",
            params=(
                data.get('first_name'),
                data.get('middle_name'),
                data.get('last_name'),
                email,
                data.get('phone_number'),
                hashed_password,
                data.get('date_of_birth'),
                data.get('gender', 'male')
            ),
            fetch='none'
        )

        return jsonify({"message": "Регистрация прошла успешно"}), 201

    except Exception as e:
        logging.error(f"Ошибка регистрации: {e}")
        return jsonify({"error": "Ошибка регистрации"}), 500


@api.route('/profile', methods=['GET'])
@jwt_required
def profile(user_id):
    user = SQL_request("SELECT * FROM users WHERE user_id = ?", params=(user_id,), fetch='one')
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({
        "user_id": user['user_id'],
        "email": user['email'],
        "first_name": user['first_name'],
        "balance": user['balance']
    }), 200


if __name__ == '__main__':
    for var in required_env_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Переменная окружения {var} не задана в .env")
    
    logging.info("Сервер запущен")
    app = Flask(__name__)
    app.register_blueprint(api)
    app.run(port=5000, debug=True)