from .main_routes import *
import base64

@api.route('/time_packages', methods=['GET'])
def time_packages():
    packages = SQL_request("SELECT * FROM time_packages WHERE is_active = TRUE", fetch='all')
    packages = [ {k: v for k, v in p.items() if k != 'image'} for p in packages ]
    return jsonify(packages), 200

@api.route('/time_packages/<int:package_id>', methods=['GET'])
def time_package(package_id):
    package = SQL_request("SELECT * FROM time_packages WHERE id = ?", (package_id,), fetch='one')
    del package['image']
    return jsonify(package), 200

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

@api.route('/buy/<string:type_product>/<int:id_product>', methods=['GET'])
@auth_decorator()
def buy_product(type_product, id_product):
    protducts = ["time_packages"]
    if type_product not in protducts:
        return jsonify({"error": "Даннный продукт не найден"}), 400
    else:
        product = SQL_request(f"SELECT * FROM {type_product} WHERE id = ?", (id_product,), fetch='one')
        message, code = buy_products(g.user, product)
        return jsonify(message), code