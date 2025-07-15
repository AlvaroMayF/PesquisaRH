# init_database.py (VERSÃO DE DEPURAÇÃO)

import os
import sys
import sqlite3

# Adiciona a raiz do projeto ao path do Python
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Agora, importamos os módulos usando o caminho a partir da raiz
from app.factory import create_app

print("--- INICIANDO SCRIPT DE DEPURAÇÃO ---")
print(f"Raiz do projeto detetada em: {project_root}")

# Cria a instância da aplicação Flask para que tenhamos o 'contexto' dela
app = create_app()

# O 'app_context' garante que o script tenha acesso às configurações
# do app, como o caminho da base de dados que definimos no factory.
with app.app_context():
    # Pega o caminho da base de dados da configuração do app
    db_path = app.config['DATABASE']
    print(f"Caminho da base de dados definido em factory.py: {db_path}")

    # Pega o caminho do schema.sql
    schema_path = os.path.join(project_root, 'app', 'src', 'config', 'schema.sql')
    print(f"A tentar ler o schema de: {schema_path}")

    try:
        # Garante que o diretório da base de dados exista
        db_dir = os.path.dirname(db_path)
        print(f"A garantir que o diretório '{db_dir}' exista...")
        os.makedirs(db_dir, exist_ok=True)

        print("A conectar à base de dados para executar o schema...")
        # Conecta diretamente à base de dados para executar o script
        conn = sqlite3.connect(db_path)

        with open(schema_path, 'r', encoding='utf-8') as f:
            print("A ler schema.sql e a executar na base de dados...")
            conn.executescript(f.read())

        conn.close()
        print("✅ Schema executado com sucesso.")

    except Exception as e:
        print(f"❌ Ocorreu um erro durante a inicialização da base de dados: {e}")

# Verificação final
print("\n--- VERIFICAÇÃO PÓS-EXECUÇÃO ---")
if os.path.exists(db_path):
    print(f"✅ SUCESSO! O ficheiro da base de dados foi encontrado em: {db_path}")
else:
    print(f"❌ FALHA! O ficheiro da base de dados NÃO foi encontrado em: {db_path}")
    print("Por favor, verifique as permissões de escrita na pasta ou se o caminho está correto.")

print("--- SCRIPT FINALIZADO ---")
