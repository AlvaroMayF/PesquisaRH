# app/src/config/db.py

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carrega variáveis do .env
# project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(_file_)))))
# dotenv_path = os.path.join(project_root, '.env')

# Carrega as variáveis a partir do caminho exato do arquivo .env
#load_dotenv(dotenv_path=dotenv_path)
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
