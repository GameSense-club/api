from .main_routes import *@api.route('/profile/all', methods=['GET'])
@auth_decorator('admin')
def profiles():
    user = SQL_request("SELECT * FROM users", fetch='all')
    return jsonify(user), 200
