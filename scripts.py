from database import *
import logging
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(levelname)s [%(asctime)s]   %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler('api.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

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