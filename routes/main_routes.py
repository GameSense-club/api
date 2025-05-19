from .registration import *
from database import SQL_request


@api.route('/', methods=['GET'])
def example():
    return jsonify({"message": "API Работает"}), 200


@api.route('/profile', methods=['GET'])
@role_required('admin')
def profile(user_id=1):
    user = SQL_request("SELECT * FROM users WHERE user_id = ?", params=(user_id,), fetch='one')
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    return jsonify({
        "user_id": user['user_id'],
        "email": user['email'],
        "first_name": user['first_name'],
        "balance": user['balance']
    }), 200

