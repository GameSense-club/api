import json
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()

DB_PATH = os.getenv("DB_PATH")

def SQL_request(query, params=(), fetch='one', jsonify_result=False):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)

            if fetch == 'all':
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [
                    {
                        col: json.loads(row[i]) if isinstance(row[i], str) and row[i].startswith('{') else row[i]
                        for i, col in enumerate(columns)
                    }
                    for row in rows
                ]
            elif fetch == 'one':
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    result = {
                        col: json.loads(row[i]) if isinstance(row[i], str) and row[i].startswith('{') else row[i]
                        for i, col in enumerate(columns)
                    }
                else:
                    result = None
            else:
                conn.commit()
                result = None

        except sqlite3.Error as e:
            print(f"Ошибка SQL: {e}")
            raise

    if jsonify_result and result is not None:
        return json.dumps(result, ensure_ascii=False, indent=2)
    return result

def create_users():
    SQL_request('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        middle_name VARCHAR(50),
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        email_confirmed BOOLEAN DEFAULT FALSE,
        phone_number VARCHAR(20),
        password_hash VARCHAR(255) NOT NULL,
        date_of_birth DATE,
        gender VARCHAR(10) DEFAULT 'male',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME,
        balance INTEGER DEFAULT 0,
        passport INTEGER DEFAULT 0,
        cart JSON,
        inventory JSON,
        tg TEXT,
        vk TEXT,
        role TEXT DEFAULT 'user',
        is_active BOOLEAN DEFAULT TRUE
    )''')

def create_verification_codes():
    SQL_request('''CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        code VARCHAR(10),
        token TEXT,  -- для восстановления пароля
        type VARCHAR(20) NOT NULL,  -- 'register', 'reset_password'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_used BOOLEAN DEFAULT FALSE
    )''')
    SQL_request('CREATE INDEX IF NOT EXISTS idx_email_type ON verification_codes (email, type)')



create_users()
create_verification_codes()