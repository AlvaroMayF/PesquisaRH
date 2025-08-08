# Arquivo: src/services/idsecure_db_service.py

import mysql.connector
from flask import current_app
import os
import time
import shutil
import subprocess
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suprime o aviso de requisição HTTPS não verificada
warnings.simplefilter('ignore', InsecureRequestWarning)


# --- FUNÇÕES DE CONEXÃO ---
def get_idsecure_db_connection():
    """Cria e retorna uma conexão com o banco de dados do iDSecure."""
    try:
        config = {
            'user': current_app.config['IDSECURE_DB_USER'],
            'password': current_app.config['IDSECURE_DB_PASSWORD'],
            'host': current_app.config['IDSECURE_DB_HOST'],
            'database': current_app.config['IDSECURE_DB_NAME'],
            'port': current_app.config['IDSECURE_DB_PORT'],
            'charset': 'utf8',
            'auth_plugin': 'mysql_native_password'
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


# --- LÓGICA DE INTEGRAÇÃO ---

def create_idsecure_user(nome, cpf, pis, senha, matricula):
    """
    Insere o usuário diretamente na tabela 'users' para obter o ID imediatamente.
    """
    conn, cursor = None, None
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            return None, "Falha ao conectar no banco iDSecure."

        try:
            parts = senha.split('-')
            senha_formatada = f"{parts[2]}{parts[1]}{parts[0]}"
        except (IndexError, AttributeError):
            senha_formatada = cpf.replace('.', '').replace('-', '')[:8]

        sql_user = """
            INSERT INTO users (
                name, registration, pis, cpf, senha, admin, inativo,
                contingency, deleted, canUseFacial, idType, expireOnDateLimit,
                blackList, idArea
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params_user = (
            nome, matricula, pis, cpf, senha_formatada,
            0, 0, 0, 0, 0, 0, 0, 0, 1
        )
        cursor.execute(sql_user, params_user)

        new_user_id = cursor.lastrowid
        conn.commit()

        print(
            f"INFO: Usuário '{nome}' criado na tabela 'users' do iDSecure. ID gerado: {new_user_id}, Matrícula: {matricula}")
        return new_user_id, None

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return None, f"Erro ao criar usuário na tabela 'users' do iDSecure: {err}"
    finally:
        close_idsecure_db_connection(conn, cursor)


def add_photo_to_idsecure(idsecure_user_id, local_photo_filename):
    """
    (LÓGICA RESTAURADA) Envia a foto .jpg para a pasta do iDSecure.
    """
    if not local_photo_filename or not idsecure_user_id or idsecure_user_id == 0:
        return False, "Dados insuficientes ou ID de usuário inválido para associar a foto."

    local_folder = current_app.config.get('FOTOS_FOLDER')
    remote_share_path = current_app.config.get('IDSECURE_IMAGES_SHARE_PATH')
    share_user = current_app.config.get('IDSECURE_SHARE_USER')
    share_password = current_app.config.get('IDSECURE_SHARE_PASSWORD')

    if not all([local_folder, remote_share_path, share_user, share_password]):
        return False, "Configurações de pasta ou credenciais de rede ausentes no .env"

    local_photo_path = os.path.join(local_folder, local_photo_filename)
    if not os.path.exists(local_photo_path):
        return False, f"Arquivo de foto local não encontrado: {local_photo_path}"

    # Voltando a salvar como .jpg e usando o nome 'usuario-ID'
    remote_filename = f"usuario-{idsecure_user_id}.jpg"
    remote_full_path = os.path.join(remote_share_path, remote_filename)

    try:
        subprocess.run(["net", "use", remote_share_path, "/delete", "/yes"], capture_output=True, check=False)
        connect_command = ["net", "use", remote_share_path, f"/user:{share_user}", share_password]
        subprocess.run(connect_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        return False, f"Falha ao autenticar na rede: {e.stderr}"

    try:
        # Apenas copia o arquivo, sem converter
        shutil.copy(local_photo_path, remote_full_path)
        print(f"INFO: Foto copiada para '{remote_full_path}'")
    except Exception as e:
        return False, f"Erro ao copiar o arquivo para a rede: {e}"
    finally:
        if os.path.exists(local_photo_path):
            os.remove(local_photo_path)

    conn, cursor = None, None
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            return False, "Arquivo copiado, mas falha ao conectar no banco iDSecure para finalizar."
        photo_timestamp = int(time.time())
        sql_update_user = "UPDATE users SET canUseFacial = 1, photoTimestamp = %s WHERE id = %s"
        cursor.execute(sql_update_user, (photo_timestamp, idsecure_user_id))
        conn.commit()
        return True, None
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return False, f"Arquivo copiado, mas falha ao atualizar o DB: {err}"
    finally:
        close_idsecure_db_connection(conn, cursor)


def trigger_idsecure_sync(user_id):
    """
    Chama a API do iDSecure para sincronizar o usuário.
    """
    base_url = current_app.config.get('IDSECURE_BASE_URL')
    api_user = current_app.config.get('IDSECURE_API_USER')
    api_password = current_app.config.get('IDSECURE_API_PASSWORD')

    if not all([base_url, api_user, api_password]):
        return False, "Configurações da API do iDSecure ausentes no .env"

    try:
        login_url = f"{base_url}/api/login"
        login_data = {"username": api_user, "password": api_password}
        login_headers = {'Content-Type': 'application/json'}

        response = requests.post(login_url, headers=login_headers, json=login_data, timeout=10, verify=False)
        response.raise_for_status()

        token = response.json().get('accessToken')
        if not token:
            return False, "Falha ao obter token de autenticação da API iDSecure (Token nulo na resposta)."

        sync_url = f"{base_url}/api/util/SyncUser/{user_id}"
        headers = {'Authorization': f'Bearer {token}'}
        sync_response = requests.get(sync_url, headers=headers, timeout=10, verify=False)
        sync_response.raise_for_status()

        print(f"INFO: Sincronização para o usuário ID {user_id} acionada com sucesso.")
        return True, None

    except requests.exceptions.HTTPError as http_err:
        error_content = "Nenhum conteúdo na resposta."
        try:
            error_content = http_err.response.text
        except:
            pass
        return False, f"Erro HTTP da API iDSecure: {http_err}. Resposta do servidor: {error_content}"
    except requests.exceptions.RequestException as e:
        return False, f"Erro de comunicação com a API do iDSecure: {e}"