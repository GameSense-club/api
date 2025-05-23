from database import *
import logging
from logging.handlers import RotatingFileHandler
import random
import string
import secrets
from mail import send_email
import json

formatter = logging.Formatter('%(levelname)s [%(asctime)s]   %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

file_handler = RotatingFileHandler('api.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def generate_token(length=32):
    return secrets.token_hex(length)

def register_send_code(email):
    code = generate_code()
    SQL_request("""
        INSERT INTO verification_codes (email, code, type)
        VALUES (?, ?, 'register')
    """, params=(email, code), fetch='none')

    # Отправляем письмо
    send_email(
        to_email=email,
        subject="Код подтверждения",
        text_body=f"Ваш код: {code}",
        html_body=f"<p>Ваш код: <strong>{code}</strong></p>"
    )

def buy_products(user, product=None, cart=None):
    if float(user['balance']) < float(product['price']):
        return {"error":"Недостаточный баланс"}, 402

    balance = float(user['balance']) - float(product['price'])
    inventory = SQL_request("SELECT inventory FROM users WHERE id = ?", params=(user['id'],), fetch='all')[0]
    inventory = (inventory['inventory'])
    product_id = str(product['id'])
    if product_id in inventory:
        inventory[product_id] += 1
    else:
        inventory[product_id] = 1
    inventory = json.dumps(inventory)
    SQL_request("UPDATE users SET inventory = ?, balance = ? WHERE id = ? ", params=(inventory, balance, user['id']), fetch='none')

    return {"message":"Оплата прошла успешно"}, 200
