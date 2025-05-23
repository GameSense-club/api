from .main_routes import *

@api.route('/profile/<int:user_id>', methods=['GET', "POST"])
@auth_decorator('admin')
def user_profile(user_id):
    if request.method == "GET":
        user = SQL_request("SELECT * FROM users WHERE id = ?", params=(user_id,), fetch='one')
        if not user:
            return jsonify({"error": "Пользователь не найден"}), 404
    
        return jsonify({
            "user_id": user['id'],
            "email": user['email'],
            "first_name": user['first_name'],
            "balance": user['balance']
        }), 200

    elif request.method == "POST":
        data = request.get_json()
        new_balance = data.get('balance')
        balance = SQL_request("SELECT balance FROM users WHERE id = ?", (user_id,), fetch='one')['balance']
        balance = balance + int(new_balance)
        SQL_request("UPDATE users SET balance = ? WHERE id = ? ", params=(balance, user_id), fetch='none')
        return jsonify({"message":"Баланс обновлён"}), 200

@api.route('/profile/all', methods=['GET'])
@auth_decorator('admin')
def profiles():
    user = SQL_request("SELECT * FROM users", fetch='all')
    return jsonify(user), 200


@api.route('/time_packages/add', methods=['POST'])
@auth_decorator('admin')
def add_time_package():
    # Проверяем, пришёл ли запрос с форм-данными
    if 'image' not in request.files:
        return jsonify({"error": "Файл изображения обязателен"}), 400

    file = request.files['image']
    data = request.form

    # Проверка наличия обязательных полей
    required_fields = ['name', 'description', 'duration_minutes', 'price', 'time_period']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Отсутствует обязательное поле: {field}"}), 400

    name = data['name']
    description = data.get('description', '')
    duration_minutes = data['duration_minutes']
    price = data['price']
    time_period = data['time_period'].lower()
    is_weekday = data.get('is_weekday', False)
    is_weekend = data.get('is_weekend', False)
    is_active = data.get('is_active', True)
    image_data = file.read()

    try: duration_minutes = int(duration_minutes)
    except: return jsonify({"error": "duration_minutes должен быть положительным целым числом"}), 400

    try: price = float(price)
    except: jsonify({"error": "price должен быть неотрицательным числом"}), 400

    # Проверки значений
    if not isinstance(duration_minutes, int) or duration_minutes <= 0:
        return jsonify({"error": "duration_minutes должен быть положительным целым числом"}), 400

    if not isinstance(price, (int, float)) or price < 0:
        return jsonify({"error": "price должен быть неотрицательным числом"}), 400

    if time_period not in ['утро', 'день', 'ночь']:
        return jsonify({"error": "time_period должен быть одним из: 'утро', 'день', 'ночь'"}), 400

    # Формируем SQL-запрос
    query = """
    INSERT INTO time_packages (
        name, 
        description, 
        duration_minutes, 
        price, 
        time_period, 
        is_weekday, 
        is_weekend, 
        is_active,
        image
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    values = (
        name,
        description,
        duration_minutes,
        price,
        time_period,
        is_weekday,
        is_weekend,
        is_active,
        image_data
    )

    try:
        SQL_request(query, values, fetch=None)
        return jsonify({
            "message": "Пакет успешно добавлен"
        }), 201
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


