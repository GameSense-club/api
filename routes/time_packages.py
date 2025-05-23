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


@api.route('/buy/<string:type_product>', methods=['POST'])
@auth_decorator()
def buy_product(type_product):
    data = request.get_json()
    product_id = data.get('id')
    quality = data.get('quality')

    protducts = ["time_packages"]
    if type_product not in protducts:
        return jsonify({"error": "Даннный продукт не найден"}), 400
    else:
        product = SQL_request(f"SELECT * FROM {type_product} WHERE id = ?", (product_id,), fetch='one')
        message, code = buy_products(g.user, product_id, type_product, quality)
        return jsonify(message), code