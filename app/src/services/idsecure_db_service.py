# Arquivo: src/services/idsecure_db_service.py (Versão FINAL e Corrigida)

import mysql.connector
from flask import current_app
import base64
import os
import time
import shutil  # Mantemos a importação para caso seja necessária, mas não a usamos na foto


def get_idsecure_db_connection():
    """Cria e retorna uma conexão com o banco de dados do iDSecure."""
    try:
        config = {
            'user': current_app.config['IDSECURE_DB_USER'],
            'password': current_app.config['IDSECURE_DB_PASSWORD'],
            'host': current_app.config['IDSECURE_DB_HOST'],
            'database': current_app.config['IDSECURE_DB_NAME'],
            'port': current_app.config['IDSECURE_DB_PORT'],
            'charset': 'utf8'
        }
        conn = mysql.connector.connect(**config)
        return conn, conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        print(f"ERRO: Falha ao conectar ao banco de dados iDSecure: {err}")
        return None, None


def close_idsecure_db_connection(conn, cursor):
    """Fecha o cursor e a conexão de forma segura."""
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


def create_idsecure_user(nome, cpf, pis):
    """
    Insere um novo usuário na tabela 'users' do IDSecure.
    A foto é tratada por outra função separada.
    """
    conn, cursor = None, None
    new_user_id = None
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            return None, "Falha ao conectar no banco iDSecure."

        # A sua lógica de create_idsecure_user não está passando o timestamp,
        # então vamos criar o usuário primeiro para obter o ID.
        sql_user = """
            INSERT INTO users (
                name, registration, pis, cpf, senha, admin, inativo,
                contingency, deleted, canUseFacial, idType, expireOnDateLimit,
                blackList, idArea
            ) VALUES ( %s, %s, %s, %s, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1)
        """
        params_user = (nome, cpf, pis, cpf)
        cursor.execute(sql_user, params_user)
        new_user_id = cursor.lastrowid
        conn.commit()
        print(f"INFO: Usuário '{nome}' criado com sucesso no iDSecure. ID: {new_user_id}")
        return new_user_id, None

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"ERRO: Falha ao inserir usuário no iDSecure: {err}")
        return None, str(err)
    finally:
        close_idsecure_db_connection(conn, cursor)


def add_photo_to_idsecure(idsecure_user_id, local_photo_filename):
    """
    Associa uma foto a um usuário no IDSecure, convertendo a imagem para Base64 e inserindo
    o template na tabela 'templates'.
    """
    if not local_photo_filename or not idsecure_user_id:
        return False, "Dados insuficientes para associar a foto."

    conn, cursor = None, None
    try:
        base_path = current_app.config.get('FOTOS_FOLDER')
        photo_path = os.path.join(base_path, local_photo_filename)

        if not os.path.exists(photo_path):
            return False, f"Arquivo de foto local não encontrado: {photo_path}"

        conn, cursor = get_idsecure_db_connection()
        if not conn:
            return False, "Falha ao conectar no banco iDSecure para inserir a foto."

        # Converte a imagem em Base64
        with open(photo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        # Insere a foto (template) na tabela 'templates'
        sql_insert_template = """
            INSERT INTO templates (
                idUser, panic, idType, templateDevice
            ) VALUES (%s, 0, 7, %s)
        """
        params_insert_template = (idsecure_user_id, encoded_string)
        cursor.execute(sql_insert_template, params_insert_template)

        # Atualiza o photoTimestamp na tabela 'users' para indicar uma nova foto
        photo_timestamp = int(time.time())
        sql_update_timestamp = "UPDATE users SET photoTimestamp = %s WHERE id = %s"
        cursor.execute(sql_update_timestamp, (photo_timestamp, idsecure_user_id))

        conn.commit()

        print(f"INFO: Template da foto inserido e photoTimestamp atualizado para o usuário ID: {idsecure_user_id}.")

        # Limpeza: remove a foto temporária após o processamento
        os.remove(photo_path)
        print(f"INFO: Foto temporária '{photo_path}' removida.")

        return True, None

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        # Captura o erro exato do MySQL, que é o que o técnico precisa
        print(f"ERRO MYSQL na função add_photo_to_idsecure: {err}")
        return False, str(err)
    except Exception as e:
        if conn: conn.rollback()
        # Captura outros erros
        print(f"ERRO GERAL na função add_photo_to_idsecure: {e}")
        return False, str(e)
    finally:
        close_idsecure_db_connection(conn, cursor)