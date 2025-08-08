# app/src/config/db.py (VERSÃO FINAL CORRIGIDA)

import os
import mysql.connector
from mysql.connector import Error

def conectar():
    """Cria e retorna uma conexão com o banco de dados do RH."""
    try:
        # A linha 'auth_plugin' foi adicionada para resolver o erro 2059.
        # Isso força o conector a usar o método de autenticação correto.
        conexao = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            auth_plugin='mysql_native_password'
        )

        if conexao.is_connected():
            return conexao

    except Error as erro:
        # Mensagem de erro foi mantida para debug futuro.
        print(f"❌ Erro ao conectar ao banco de dados RH: {erro}")
        return None

    return None

# Alias para manter a compatibilidade com o resto do código.
get_db_connection = conectar