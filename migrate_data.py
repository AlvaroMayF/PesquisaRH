# migrate_data.py

import os
import sys
import pandas as pd
import mysql.connector
import sqlite3
from dotenv import load_dotenv

# Garante que o script encontre os módulos do projeto
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Carrega as variáveis de ambiente (usuário, senha do MySQL)
load_dotenv()

# --- CONFIGURAÇÕES ---
# Caminho para o novo banco de dados SQLite
SQLITE_DB_PATH = os.path.join(project_root, 'instance', 'pesquisa.db')

# Lista de todas as tabelas que queremos migrar
TABLES_TO_MIGRATE = [
    'unidades',
    'surveys',
    'colaboradores',
    'feriados',
    'admins',
    'audit_logs',
    'comunicados',
    'form_questions',
    'responses',
    'colaborador_survey_status',
    'form_options',
    'response_answers'
]


# --- FUNÇÕES DE CONEXÃO ---
def connect_mysql():
    """Conecta ao banco de dados MySQL local."""
    try:
        print("Conectando ao MySQL...")
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        if conn.is_connected():
            print("✅ Conexão com MySQL estabelecida.")
            return conn
    except mysql.connector.Error as e:
        print(f"❌ Erro ao conectar ao MySQL: {e}")
        return None


def connect_sqlite():
    """Conecta ao arquivo de banco de dados SQLite."""
    try:
        print("Conectando ao SQLite...")
        conn = sqlite3.connect(SQLITE_DB_PATH)
        print("✅ Conexão com SQLite estabelecida.")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Erro ao conectar ao SQLite: {e}")
        return None


# --- SCRIPT PRINCIPAL ---
def migrate_data():
    """Lê dados do MySQL e insere no SQLite, tabela por tabela."""
    mysql_conn = connect_mysql()
    sqlite_conn = connect_sqlite()

    if not mysql_conn or not sqlite_conn:
        print("Não foi possível estabelecer conexão com um dos bancos de dados. Abortando.")
        return

    try:
        for table_name in TABLES_TO_MIGRATE:
            print(f"\nIniciando migração da tabela: '{table_name}'...")

            # 1. Lê a tabela do MySQL para um DataFrame do Pandas
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql(query, mysql_conn)

            if df.empty:
                print(f"-> Tabela '{table_name}' está vazia no MySQL. Pulando.")
                continue

            print(f"-> {len(df)} registros lidos do MySQL.")

            # 2. Escreve o DataFrame para a tabela correspondente no SQLite
            # 'if_exists='append'' adiciona os dados sem apagar a tabela
            # 'index=False' garante que o índice do DataFrame não seja salvo como uma coluna
            df.to_sql(table_name, sqlite_conn, if_exists='append', index=False)

            print(f"-> Dados inseridos com sucesso em '{table_name}' no SQLite.")

        print("\n🎉 Migração de dados concluída com sucesso!")

    except Exception as e:
        print(f"\n❌ Ocorreu um erro durante a migração: {e}")
    finally:
        # 3. Fecha as conexões
        if mysql_conn:
            mysql_conn.close()
            print("\nConexão com MySQL fechada.")
        if sqlite_conn:
            sqlite_conn.close()
            print("Conexão com SQLite fechada.")


# Executa o script quando chamado pelo terminal
if __name__ == '__main__':
    migrate_data()
