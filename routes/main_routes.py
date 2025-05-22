from database import SQL_request
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


@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200


@api.route('/profile', methods=['GET'])
@auth_decorator()
def profile():
    return jsonify({
        'id': g.user['user_id'],
        'email': g.user["email"],
    }), 200

@api.route('/profile/<int:user_id>', methods=['GET'])
@auth_decorator('admin')
def user_profile(user_id):
    user = SQL_request("SELECT * FROM users WHERE user_id = ?", params=(user_id,), fetch='one')
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({
        "user_id": user['user_id'],
        "email": user['email'],
        "first_name": user['first_name'],
        "balance": user['balance']
    }), 200
