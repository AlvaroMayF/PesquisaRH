# app/src/config/db.py

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

def conectar():
    try:
        conexao = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

        if conexao.is_connected():
            print("✅ Conexão estabelecida com sucesso!")
            return conexao

    except Error as erro:
        print(f"❌ Erro ao conectar ao banco de dados: {erro}")
        return None

    return None

# Alias opcional para compatibilidade com outras partes do código
get_db_connection = conectar

# Teste direto
if __name__ == '__main__':
    conn = conectar()
    if conn:
        print("✔️ Teste de conexão finalizado com sucesso.")
        conn.close()
