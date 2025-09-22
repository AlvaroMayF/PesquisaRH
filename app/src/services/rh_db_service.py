# Arquivo: src/services/rh_db_service.py

import mysql.connector
from flask import current_app


def get_rh_db_connection():
    """Estabelece conexão com o banco de dados do RH."""
    print("DEBUG: [RH-DB] Tentando obter conexão com o banco de dados principal do RH...")
    try:
        # IMPORTANTE: Você precisará adicionar essas configurações no seu .env
        config = {
            'user': current_app.config['DB_USER'],
            'password': current_app.config['DB_PASSWORD'],
            'host': current_app.config['DB_HOST'],
            'database': current_app.config['DB_NAME'],
            'port': current_app.config['DB_PORT'],
        }
        conn = mysql.connector.connect(**config)
        print("DEBUG: [RH-DB] Conexão com o banco RH estabelecida com sucesso.")
        return conn, conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        # Se esta mensagem aparecer, o problema está nas suas credenciais do .env ou na rede.
        print(f"ERRO CRÍTICO: [RH-DB] Falha ao conectar ao banco de dados do RH: {err}")
        return None, None


def close_rh_db_connection(conn, cursor):
    """Fecha a conexão com o banco de dados do RH."""
    print("DEBUG: [RH-DB] Fechando conexão com o banco RH.")
    if cursor:
        try:
            cursor.close()
        except:
            pass
    if conn and conn.is_connected():
        try:
            conn.close()
        except:
            pass


def create_colaborador(data):
    """
    Cria um novo colaborador no banco de dados do RH.
    'data' é um dicionário contendo os dados do formulário.
    Ex: {'nome': 'Fulano', 'cpf': '123...', 'coren': 'COREN123'}
    """
    conn, cursor = None, None
    print(f"DEBUG: [RH-DB] Iniciando criação de colaborador com os dados: {data}")
    try:
        conn, cursor = get_rh_db_connection()
        if not conn:
            print("ERRO CRÍTICO: [RH-DB] A conexão com o banco RH retornou None. Abortando criação.")
            return None, "Falha ao conectar no banco de dados do RH."

        # Monta a query de forma dinâmica com base nos dados recebidos
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO colaboradores ({fields}) VALUES ({placeholders})"

        params = list(data.values())

        print(f"DEBUG: [RH-DB] Executando SQL: {sql}")
        print(f"DEBUG: [RH-DB] Com parâmetros: {params}")
        cursor.execute(sql, params)
        new_id = cursor.lastrowid
        conn.commit()

        print(f"SUCESSO: [RH-DB] Colaborador '{data.get('nome')}' inserido com ID {new_id}.")
        return new_id, None

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        # Esta mensagem mostrará o erro exato do banco de dados (ex: coluna não existe, valor inválido, etc.)
        print(f"ERRO CRÍTICO: [RH-DB] Ocorreu um erro de MySQL na criação: {err}")
        return None, f"Erro no banco de dados do RH: {err}"
    finally:
        close_rh_db_connection(conn, cursor)