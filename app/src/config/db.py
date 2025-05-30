# app/src/config/db.py

import os
from mysql.connector import connect, Error
from dotenv import load_dotenv

# carrega o .env que fica no root do projeto
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

def get_db_connection():
    try:
        conn = connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "pesquisa_rh"),
            autocommit=True
        )
        return conn
    except Error as e:
        print(f"Erro ao conectar no MySQL: {e}")
        raise
