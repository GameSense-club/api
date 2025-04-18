import logging
from database import *

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(asctime)s]   %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def user_data(id=None, email=None, phone=None): # получение данных пользователя
    conditions = []
    params = []
    if id is not None:
        conditions.append("user_id = ?")
        params.append(id)
    if email is not None:
        conditions.append("email = ?")
        params.append(email)
    if phone is not None:
        conditions.append("phone_number = ?")
        params.append(phone)
    if not conditions:
        logging.error("Укажите id, email или phone")
        return None
    query = "SELECT * FROM users WHERE " + " AND ".join(conditions)
    return SQL_request(query, params)