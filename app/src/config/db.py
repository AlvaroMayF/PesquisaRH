# app/src/config/db.py (VERSÃO COMPLETA E CORRIGIDA)

import sqlite3
import os
from flask import current_app, g


def get_db_connection():
    """
    Cria e gere uma conexão com a base de dados SQLite.
    A conexão é armazenada no contexto 'g' do Flask para ser reutilizada
    durante o mesmo pedido, o que é mais eficiente.
    """
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )

        # Esta linha é crucial! Ela faz com que os resultados das queries
        # venham como dicionários (ex: row['coluna']), parecido com o que você já usava,
        # em vez de tuplas (ex: row[0]).
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db_connection(e=None):
    """Fecha a conexão com a base de dados no final do pedido."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


# --- A FUNÇÃO QUE ESTAVA A FALTAR ---
def init_db():
    """Lê e executa o ficheiro schema.sql para criar as tabelas."""
    db = get_db_connection()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    print("Base de dados inicializada a partir do schema.sql.")


# ------------------------------------

def init_db_command(app):
    """Cria um comando de terminal 'flask init-db'."""

    @app.cli.command('init-db')
    def cli_command():
        """Limpa os dados existentes e cria novas tabelas."""
        init_db()
        print("Comando 'init-db' executado com sucesso.")


def init_app(app):
    """Regista as funções de gestão da base de dados com a aplicação Flask."""
    app.teardown_appcontext(close_db_connection)
    init_db_command(app)


# Mantém o alias 'conectar' para compatibilidade com o resto do seu código
conectar = get_db_connection
