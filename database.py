import json
import sqlite3

DB_NAME = 'database.db'
DB_PATH = f"{DB_NAME}"

def SQL_request(request, params=(), all_data=None, return_json=None): # выполнение SQL запросов
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    result = None
    
    if request.strip().lower().startswith('select'):
        cursor.execute(request, params)
        if all_data is None:
            raw_result = cursor.fetchone()
        else:
            raw_result = cursor.fetchall()

        if raw_result is not None and cursor.description:
            columns = [col[0] for col in cursor.description]
            data = {}
            for col, value in zip(columns, raw_result):
                try:
                    data[col] = json.loads(raw_result)
                except: pass
            result = data
        else:
            result = raw_result
        
        connect.close()
        if return_json:
            return json.dumps(result)
        return result
    else:
        cursor.execute(request, params)
        connect.commit()
        connect.close()
        return None

def create_users():
    SQL_request('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        middle_name VARCHAR(50),
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone_number VARCHAR(20),
        password VARCHAR(255) NOT NULL,
        date_of_birth DATE,
        gender VARCHAR(10) DEFAULT 'male',
        joined DATETIME,
        last_login DATETIME,
        balance INTEGER DEFAULT 0,
        passport INTEGER DEFAULT 0,
        cart JSON,
        inventory JSON,
        tg TEXT,
        vk TEXT,
        role TEXT DEFAULT 'user'
    )''')

def create_verification_codes():
    SQL_request('''CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        code VARCHAR(10) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        type VARCHAR(20) NOT NULL
    )''')
    SQL_request('CREATE INDEX IF NOT EXISTS idx_email_type ON verification_codes (email, type)')



create_users()
create_verification_codes()