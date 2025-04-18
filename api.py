from flask import Flask, jsonify, Blueprint, request, abort
import config
from scripts import *
from flask_cors import CORS

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

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')  # Это может быть email или телефон
    password = data.get('password')
    if not identifier or not password:
        return jsonify({"error": "Укажите логин или пароль!"}), 400

    user = user_data(email=identifier)
    if user is None:
        user = user_data(phone=identifier)
    if user is None:
        return jsonify({"error": "Пользователь не найден!"}), 400

    return jsonify(user), 200



if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(api)
    app.run(port=5000, debug=True)