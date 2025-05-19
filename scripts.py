from database import *
import logging
from logging.handlers import RotatingFileHandler
import random
import string
import secrets

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