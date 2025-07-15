# factory.py

import os
import sys
from flask import Flask, send_from_directory, session, redirect, url_for, request
from markupsafe import escape, Markup
from datetime import timedelta

# Adiciona a pasta 'app' ao path do Python para garantir que os imports de 'src' funcionem
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import dos blueprints de rota
from src.routers.admin import admin
from src.routers.adminLogin import adminLogin
from src.routers.homeView import home as home_bp
from src.routers.logout import logout_bp
from src.routers.analitico import analitico_bp
from src.routers.pesquisa import pesquisa_bp
from src.routers.comunicados import comunicados_bp
from src.routers.novo_colaborador import novo_colaborador_bp
from src.routers.novo_comunicado import novo_comunicado_bp
from src.routers.admin_feriados import admin_feriados_bp
from src.routers.beneficios import beneficios_bp
from src.routers.auth import auth_bp
from src.routers.pesquisas_lista import pesquisas_lista_bp
from src.routers.admin_surveys import admin_surveys_bp

# Imports para a rota de setup do banco de dados
from src.config.db import init_db
from src.config.seeder import seed_data


def create_app():
    # Define os caminhos para as pastas de templates e assets (que agora são os próprios templates)
    template_folder = os.path.join(app_dir, 'src', 'views')

    app = Flask(__name__, instance_relative_config=True, template_folder=template_folder)

    # --- CONFIGURAÇÃO CENTRALIZADA ---
    is_production = os.getenv('RENDER', False)
    db_path = os.path.join('/var/data', 'pesquisa.db') if is_production else os.path.join(app.instance_path,
                                                                                          'pesquisa.db')

    app.config.from_mapping(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev_key_super_secreta'),
        DATABASE=db_path,
        UPLOAD_FOLDER=os.path.join(app_dir, 'src', 'uploads'),
        SEND_FILE_MAX_AGE_DEFAULT=31536000
    )

    # Garante que os diretórios necessários existam
    if is_production:
        os.makedirs('/var/data', exist_ok=True)
    else:
        os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- INICIALIZAÇÃO DE EXTENSÕES ---
    # Removido 'from src.config import db' e 'db.init_app(app)' pois a nova abordagem
    # usa o 'db.py' diretamente quando necessário.
    from src.config import db as db_manager
    db_manager.init_app(app)

    # --- LÓGICA DA APLICAÇÃO ---
    app.permanent_session_lifetime = timedelta(minutes=30)

    @app.before_request
    def require_login():
        session.permanent = True
        # Adicionadas as rotas de setup e assets às exceções
        allowed_endpoints = ['auth.login', 'static', 'serve_view_file', 'setup_database_route']
        if 'colaborador_id' not in session and request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth.login'))

    def nl2br(value):
        return Markup(escape(value).replace('\n', '<br>\n'))

    app.jinja_env.filters['nl2br'] = nl2br

    # --- REGISTRO DOS BLUEPRINTS ---
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(adminLogin)
    app.register_blueprint(home_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(analitico_bp)
    app.register_blueprint(pesquisa_bp)
    app.register_blueprint(comunicados_bp)
    app.register_blueprint(novo_colaborador_bp)
    app.register_blueprint(novo_comunicado_bp)
    app.register_blueprint(admin_feriados_bp)
    app.register_blueprint(beneficios_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pesquisas_lista_bp)
    app.register_blueprint(admin_surveys_bp)

    # --- ROTAS ESPECIAIS ---

    # Rota para servir os ficheiros CSS/JS que estão DENTRO da pasta 'views'
    @app.route('/view_assets/<path:filename>')
    def serve_view_file(filename):
        return send_from_directory(app.template_folder, filename)

    # Rota para servir os ficheiros da pasta de uploads
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # --- ROTA SECRETA DE SETUP ---
    @app.route('/setup-database-one-time/<secret_key>')
    def setup_database_route(secret_key):
        # Defina uma chave secreta para proteger esta rota
        SETUP_SECRET_KEY = "minha-chave-super-secreta-12345"

        if secret_key != SETUP_SECRET_KEY:
            return "Chave secreta inválida.", 403

        try:
            print("Iniciando setup do banco de dados via rota secreta...")
            # Passo 1: Cria as tabelas a partir do schema.sql
            init_db()
            print("Tabelas criadas com sucesso.")

            # Passo 2: Popula as tabelas com os dados iniciais
            seed_data()
            print("Dados inseridos com sucesso.")

            return "<h1>Sucesso!</h1><p>O banco de dados foi inicializado e populado. Esta rota não deve ser usada novamente.</p>", 200
        except Exception as e:
            return f"<h1>Erro!</h1><p>Ocorreu um erro durante o setup: {e}</p>", 500

    return app