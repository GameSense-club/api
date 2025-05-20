from flask import Blueprint, jsonify, request, abort, g
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
import jwt
import datetime
import logging
from mail import send_email
from middleware import setup_middleware, auth_decorator
from database import SQL_request
import config
from utils import *

SECRET_KEY = config.SECRET_KEY

api = Blueprint('api', __name__)

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

    if user["email_confirmed"] == 0:
        register_send_code(user["email"])
        return jsonify({"message": "Аккаунт не подтверждён. Код отправлен на ваш email"}), 200

    else:
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

        register_send_code(email)
        return jsonify({"message": "Код отправлен на ваш email"}), 200

    except Exception as e:
        logging.error(f"Ошибка регистрации: {e}")
        return jsonify({"error": "Ошибка регистрации"}), 500

@api.route('/register/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({"error": "Email и код обязательны"}), 400

    record = SQL_request("""
        SELECT * FROM verification_codes
        WHERE email = ? AND code = ? AND type = 'register'
        ORDER BY created_at DESC LIMIT 1
    """, params=(email, code), fetch='one')

    if not record:
        return jsonify({"error": "Неверный код или истёк срок действия"}), 400

    if record['is_used']:
        return jsonify({"error": "Этот код уже использован"}), 400

    # Обновляем запись как использованную
    SQL_request("""
        UPDATE verification_codes SET is_used = TRUE
        WHERE id = ?
    """, params=(record['id'],), fetch='none')

    SQL_request("""
        UPDATE users SET email_confirmed = TRUE
        WHERE email = ?
    """, params=(email,), fetch='none')

    return jsonify({"message": "Email подтверждён"}), 200