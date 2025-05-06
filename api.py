from flask import Flask, jsonify, Blueprint, request, abort
import config
from scripts import *
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    jwt_required, get_jwt_identity
)
from werkzeug.security import generate_password_hash, check_password_hash
import random
import datetime

if __name__ != '__main__':
    CORS(app)

VERSION = "test"
ALLOWED_API_KEYS = config.API_KEYS
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


# РОУТЫ
@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200

def generate_code(length=6):
    return ''.join(random.choice('0123456789') for _ in range(length))

def send_email(email, code):
    # Заглушка для отправки email
    print(f"Код для {email}: {code}")

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    
    if not email or '@' not in email:
        abort(400, description="Некорректный email")
    
    if SQL_request('SELECT email FROM users WHERE email = ?', (email,)):
        abort(409, description="Email уже зарегистрирован")
    
    code = generate_code()
    SQL_request('''INSERT INTO verification_codes (email, code, type) 
                   VALUES (?, ?, ?)''', 
                (email, code, 'registration'))
    send_email(email, code)
    
    return jsonify(message="Код подтверждения отправлен"), 200

@api.route('/auth/verify', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    user_data = data.get('user_data')
    
    verification = SQL_request('''SELECT * FROM verification_codes 
                               WHERE email = ? AND code = ? AND type = ? 
                               ORDER BY created_at DESC LIMIT 1''',
                               (email, code, 'registration'), all_data=True)
    
    if not verification:
        abort(400, description="Неверный код или email")
    
    try:
        hashed_pw = generate_password_hash(user_data['password'])
        SQL_request('''INSERT INTO users (
            email, password, first_name, last_name, 
            phone_number, date_of_birth, joined
        ) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
            email,
            hashed_pw,
            user_data.get('first_name', ''),
            user_data.get('last_name', ''),
            user_data.get('phone_number', ''),
            user_data.get('date_of_birth', ''),
            datetime.datetime.now()
        ))
        SQL_request('DELETE FROM verification_codes WHERE email = ? AND type = ?', 
                    (email, 'registration'))
    except Exception as e:
        abort(500, description=str(e))
    
    return jsonify(message="Регистрация успешна"), 201

@api.route('/auth/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    
    user = SQL_request('SELECT * FROM users WHERE email = ?', (email,))
    if not user or not check_password_hash(user['password'], password):
        abort(401, description="Неверные учетные данные")
    
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token), 200

@api.route('/auth/forgot_password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    if not email:
        abort(400, description="Укажите email")
    
    user = SQL_request('SELECT email FROM users WHERE email = ?', (email,))
    if not user:
        abort(404, description="Пользователь не найден")
    
    code = generate_code()
    SQL_request('''INSERT INTO verification_codes (email, code, type) 
                 VALUES (?, ?, ?)''', 
              (email, code, 'password_reset'))
    send_email(email, code)
    
    return jsonify(message="Код для сброса пароля отправлен"), 200

@api.route('/auth/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    code = data.get('code')
    new_password = data.get('new_password')
    
    verification = SQL_request('''SELECT * FROM verification_codes 
                               WHERE email = ? AND code = ? AND type = ? 
                               ORDER BY created_at DESC LIMIT 1''',
                               (email, code, 'password_reset'), all_data=True)
    
    if not verification:
        abort(400, description="Неверный код или email")
    
    hashed_pw = generate_password_hash(new_password)
    SQL_request('UPDATE users SET password = ? WHERE email = ?', 
               (hashed_pw, email))
    SQL_request('DELETE FROM verification_codes WHERE email = ? AND type = ?', 
               (email, 'password_reset'))
    
    return jsonify(message="Пароль успешно изменен"), 200


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(api)
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET
    jwt = JWTManager(app)
    app.run(port=5000, debug=True)