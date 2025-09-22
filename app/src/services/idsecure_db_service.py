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
    """Tenta conectar ao banco de dados do iDSecure."""
    print("DEBUG: [iDSecure-DB] Tentando obter conexão com o banco de dados iDSecure...")
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
        print("DEBUG: [iDSecure-DB] Conexão com iDSecure estabelecida com sucesso.")
        return conn, conn.cursor(dictionary=True)
    except mysql.connector.Error as err:
        # Este erro é crucial. Se aparecer, verifique suas variáveis de ambiente e a rede.
        print(f"ERRO CRÍTICO: [iDSecure-DB] Falha ao conectar ao banco de dados iDSecure: {err}")
        return None, None


def close_idsecure_db_connection(conn, cursor):
    """Fecha a conexão com o banco de dados do iDSecure."""
    print("DEBUG: [iDSecure-DB] Fechando conexão com iDSecure.")
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

def check_user_exists(matricula):
    """Verifica se um usuário já existe no iDSecure."""
    print(f"DEBUG: [iDSecure-DB] Verificando se a matrícula '{matricula}' existe...")
    conn, cursor = None, None
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            return False
        cursor.execute("SELECT id FROM users WHERE id = %s", (matricula,))
        exists = cursor.fetchone() is not None
        print(f"DEBUG: [iDSecure-DB] Matrícula '{matricula}' existe? {'Sim' if exists else 'Não'}.")
        return exists
    except Exception as e:
        print(f"ERRO: [iDSecure-DB] Falha ao verificar existência do usuário {matricula}: {e}")
        return False
    finally:
        close_idsecure_db_connection(conn, cursor)


def create_idsecure_user(nome, cpf, pis, senha, matricula, setor=None):
    """Cria um novo usuário no banco de dados do iDSecure."""
    conn, cursor = None, None
    print(f"DEBUG: [iDSecure-DB] Iniciando criação de usuário iDSecure para matrícula: {matricula}")
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            print("ERRO CRÍTICO: [iDSecure-DB] A conexão com o banco iDSecure retornou None. Abortando criação.")
            return None, "Falha ao conectar no banco iDSecure."

        try:
            parts = senha.split('-')
            senha_formatada = f"{parts[2]}{parts[1]}{parts[0]}"
        except (IndexError, AttributeError):
            senha_formatada = cpf.replace('.', '').replace('-', '')[:8]

        sql_user = """
            INSERT INTO users (
                id, name, registration, idDevice, pis, cpf, senha, admin, inativo,
                contingency, deleted, canUseFacial, idType, expireOnDateLimit,
                blackList, idArea
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params_user = (
            matricula, nome, matricula, matricula, pis, cpf, senha_formatada,
            0, 0, 0, 0, 0, 0, 0, 0, 1
        )
        print("DEBUG: [iDSecure-DB] Executando inserção na tabela 'users'...")
        cursor.execute(sql_user, params_user)
        new_user_id = matricula
        print(f"INFO: [iDSecure-DB] Usuário '{nome}' (ID: {new_user_id}) inserido em 'users'.")

        if setor:
            print(f"DEBUG: [iDSecure-DB] Procurando grupo para o setor: '{setor}'")
            sql_find_group = "SELECT id FROM groups WHERE name = %s"
            cursor.execute(sql_find_group, (setor,))
            group_record = cursor.fetchone()
            if not group_record:
                print(f"ERRO: [iDSecure-DB] Setor '{setor}' não foi encontrado. Executando rollback.")
                conn.rollback()
                return None, f"Erro: O departamento '{setor}' não foi encontrado no iDSecure."

            group_id = group_record['id']
            sql_link_user_group = "INSERT INTO usergroups (idUser, idGroup, isVisitor) VALUES (%s, %s, %s)"
            print(f"DEBUG: [iDSecure-DB] Vinculando usuário {new_user_id} ao grupo {group_id}...")
            cursor.execute(sql_link_user_group, (new_user_id, group_id, 0))
            print(f"INFO: [iDSecure-DB] Usuário {new_user_id} vinculado ao Grupo {group_id}.")

        conn.commit()
        print(f"SUCESSO: [iDSecure-DB] Transação concluída para o usuário '{nome}'.")
        return new_user_id, None

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        # Esta é a mensagem de erro que provavelmente está causando o problema
        print(f"ERRO CRÍTICO: [iDSecure-DB] Ocorreu um erro de MySQL na criação: {err}")
        if err.errno == 1062:
            return None, f"Erro Crítico: O ID/Matrícula '{matricula}' já existe."
        return None, f"Erro de banco de dados na criação: {err}"
    finally:
        close_idsecure_db_connection(conn, cursor)


def update_idsecure_user(matricula, nome, pis, setor):
    """Atualiza um usuário existente no iDSecure."""
    conn, cursor = None, None
    print(f"DEBUG: [iDSecure-DB] Iniciando atualização do usuário iDSecure para matrícula: {matricula}")
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            print(f"ERRO CRÍTICO: [iDSecure-DB] Falha de conexão ao tentar ATUALIZAR usuário {matricula}.")
            return False, "Falha ao conectar no banco iDSecure."

        sql_update_user = "UPDATE users SET name = %s, pis = %s WHERE id = %s"
        cursor.execute(sql_update_user, (nome, pis, matricula))
        print(f"INFO: [DB-Update] Dados do usuário {matricula} atualizados em 'users'.")

        sql_delete_links = "DELETE FROM usergroups WHERE idUser = %s"
        cursor.execute(sql_delete_links, (matricula,))
        print(f"INFO: [DB-Update] Vínculos de grupo antigos para o usuário {matricula} removidos.")

        if setor:
            sql_find_group = "SELECT id FROM groups WHERE name = %s"
            cursor.execute(sql_find_group, (setor,))
            group_record = cursor.fetchone()
            if not group_record:
                conn.rollback()
                print(f"ERRO: [iDSecure-DB] Novo setor '{setor}' não encontrado ao ATUALIZAR. Rollback.")
                return False, f"Erro: O novo departamento '{setor}' não foi encontrado."
            group_id = group_record['id']
            sql_insert_link = "INSERT INTO usergroups (idUser, idGroup, isVisitor) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert_link, (matricula, group_id, 0))
            print(f"INFO: [DB-Update] Usuário {matricula} vinculado ao novo grupo {group_id}.")
        else:
            print(f"INFO: [DB-Update] Nenhum setor fornecido, usuário {matricula} ficou sem grupo.")

        conn.commit()
        print(f"SUCESSO: [iDSecure-DB] Transação de atualização para o usuário {matricula} concluída.")
        return True, None
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"ERRO CRÍTICO: [iDSecure-DB] Ocorreu um erro de MySQL na atualização: {err}")
        return False, f"Erro de banco de dados na atualização: {err}"
    finally:
        close_idsecure_db_connection(conn, cursor)


def set_idsecure_user_status(matricula, is_active):
    """Define o status (ativo/inativo) de um usuário no iDSecure."""
    conn, cursor = None, None
    print(f"DEBUG: [iDSecure-DB] Tentando alterar status do usuário {matricula} para is_active={is_active}")
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            print(f"ERRO CRÍTICO: [iDSecure-DB] Falha de conexão ao tentar ATUALIZAR STATUS do usuário {matricula}.")
            return False, "Falha ao conectar no banco iDSecure para atualizar status."

        inativo_flag = 1 - is_active
        sql = "UPDATE users SET inativo = %s WHERE id = %s"
        cursor.execute(sql, (inativo_flag, matricula))
        conn.commit()

        status_text = "INATIVADO" if inativo_flag == 1 else "ATIVADO"
        print(f"SUCESSO: [DB-Status] Usuário {matricula} foi {status_text} no iDSecure.")
        return True, None
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"ERRO CRÍTICO: [iDSecure-DB] Ocorreu um erro de MySQL na atualização de status: {err}")
        return False, f"Erro de banco de dados ao atualizar status: {err}."
    finally:
        close_idsecure_db_connection(conn, cursor)


def add_photo_to_idsecure(idsecure_user_id, local_photo_filename):
    """Adiciona a foto de um usuário no compartilhamento de rede do iDSecure."""
    print(f"DEBUG: [iDSecure-PHOTO] Iniciando processo de adicionar foto para user_id: {idsecure_user_id}")
    if not local_photo_filename or not idsecure_user_id or idsecure_user_id == 0:
        print("ERRO: [iDSecure-PHOTO] Dados insuficientes para adicionar foto.")
        return False, "Dados insuficientes ou ID de usuário inválido para associar a foto."

    local_folder = current_app.config.get('FOTOS_FOLDER')
    remote_share_path = current_app.config.get('IDSECURE_IMAGES_SHARE_PATH')
    share_user = current_app.config.get('IDSECURE_SHARE_USER')
    share_password = current_app.config.get('IDSECURE_SHARE_PASSWORD')

    if not all([local_folder, remote_share_path, share_user, share_password]):
        print("ERRO: [iDSecure-PHOTO] Configurações de rede (pasta, usuário, senha) ausentes no .env")
        return False, "Configurações de pasta ou credenciais de rede ausentes no .env"

    local_photo_path = os.path.join(local_folder, local_photo_filename)
    if not os.path.exists(local_photo_path):
        print(f"ERRO: [iDSecure-PHOTO] Arquivo de foto local não encontrado em: {local_photo_path}")
        return False, f"Arquivo de foto local não encontrado: {local_photo_path}"

    remote_filename = f"usuario-{idsecure_user_id}.jpg"
    remote_full_path = os.path.join(remote_share_path, remote_filename)

    try:
        print(f"DEBUG: [iDSecure-PHOTO] Tentando autenticar na rede: {remote_share_path}")
        subprocess.run(["net", "use", remote_share_path, "/delete", "/yes"], capture_output=True, check=False)
        connect_command = ["net", "use", remote_share_path, f"/user:{share_user}", share_password]
        subprocess.run(connect_command, check=True, capture_output=True, text=True)
        print("DEBUG: [iDSecure-PHOTO] Autenticação na rede bem-sucedida.")
    except subprocess.CalledProcessError as e:
        print(
            f"ERRO CRÍTICO: [iDSecure-PHOTO] Falha ao autenticar na rede. Verifique usuário/senha do compartilhamento. Detalhes: {e.stderr}")
        return False, f"Falha ao autenticar na rede: {e.stderr}"

    try:
        print(f"DEBUG: [iDSecure-PHOTO] Copiando '{local_photo_path}' para '{remote_full_path}'")
        shutil.copy(local_photo_path, remote_full_path)
        print(f"INFO: [iDSecure-PHOTO] Foto copiada para '{remote_full_path}'")
    except Exception as e:
        print(f"ERRO CRÍTICO: [iDSecure-PHOTO] Falha ao copiar arquivo para a rede: {e}")
        return False, f"Erro ao copiar o arquivo para a rede: {e}"
    finally:
        if os.path.exists(local_photo_path):
            #os.remove(local_photo_path)
            print(f"DEBUG: [iDSecure-PHOTO] Arquivo de foto local '{local_photo_path}' removido.")

    conn, cursor = None, None
    try:
        conn, cursor = get_idsecure_db_connection()
        if not conn:
            print("ERRO CRÍTICO: [iDSecure-PHOTO] Foto copiada, mas falha ao conectar no DB para finalizar.")
            return False, "Arquivo copiado, mas falha ao conectar no banco iDSecure para finalizar."

        photo_timestamp = int(time.time())
        sql_update_user = "UPDATE users SET canUseFacial = 1, photoTimestamp = %s WHERE id = %s"
        print(
            f"DEBUG: [iDSecure-PHOTO] Atualizando tabela 'users' para user_id {idsecure_user_id} com novo timestamp de foto.")
        cursor.execute(sql_update_user, (photo_timestamp, idsecure_user_id))
        conn.commit()
        print(f"SUCESSO: [iDSecure-PHOTO] Processo de foto para user_id {idsecure_user_id} concluído.")
        return True, None
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"ERRO CRÍTICO: [iDSecure-PHOTO] Foto copiada, mas falha ao atualizar o DB: {err}")
        return False, f"Arquivo copiado, mas falha ao atualizar o DB: {err}"
    finally:
        close_idsecure_db_connection(conn, cursor)


def trigger_idsecure_sync(user_id):
    """Aciona a API de sincronização do iDSecure para um usuário."""
    print(f"DEBUG: [iDSecure-API] Acionando sincronização via API para user_id: {user_id}")
    base_url = current_app.config.get('IDSECURE_BASE_URL')
    api_user = current_app.config.get('IDSECURE_API_USER')
    api_password = current_app.config.get('IDSECURE_API_PASSWORD')

    if not all([base_url, api_user, api_password]):
        print("ERRO: [iDSecure-API] Configurações da API (URL, usuário, senha) ausentes no .env")
        return False, "Configurações da API do iDSecure ausentes no .env"

    try:
        login_url = f"{base_url}/api/login"
        login_data = {"username": api_user, "password": api_password}
        login_headers = {'Content-Type': 'application/json'}
        print("DEBUG: [iDSecure-API] Autenticando na API iDSecure...")
        response = requests.post(login_url, headers=login_headers, json=login_data, timeout=10, verify=False)
        response.raise_for_status()
        token = response.json().get('accessToken')

        if not token:
            print("ERRO: [iDSecure-API] Falha na autenticação da API, token nulo.")
            return False, "Falha ao obter token de autenticação da API iDSecure (Token nulo na resposta)."

        print("DEBUG: [iDSecure-API] Autenticação bem-sucedida. Acionando sync...")
        sync_url = f"{base_url}/api/util/SyncUser/{user_id}"
        headers = {'Authorization': f'Bearer {token}'}
        sync_response = requests.get(sync_url, headers=headers, timeout=10, verify=False)
        sync_response.raise_for_status()

        print(f"SUCESSO: [iDSecure-API] Sincronização para o usuário ID {user_id} acionada com sucesso.")
        return True, None
    except requests.exceptions.HTTPError as http_err:
        error_content = "Nenhum conteúdo na resposta."
        try:
            error_content = http_err.response.text
        except:
            pass
        print(
            f"ERRO CRÍTICO: [iDSecure-API] Erro HTTP. Status: {http_err.response.status_code}, Resposta: {error_content}")
        return False, f"Erro HTTP da API iDSecure: {http_err}. Resposta do servidor: {error_content}"
    except requests.exceptions.RequestException as e:
        print(f"ERRO CRÍTICO: [iDSecure-API] Erro de comunicação com a API: {e}")
        return False, f"Erro de comunicação com a API do iDSecure: {e}"