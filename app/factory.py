# factory.py
# Forçando a atualização para o deploy de 15/07

import os
import sys
from flask import Flask, send_from_directory, session, redirect, url_for, request
from markupsafe import escape, Markup
from datetime import timedelta

# Adiciona a raiz do projeto ao path do Python para garantir que os imports funcionem
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import dos blueprints de rota
from app.src.routers.admin import admin
from app.src.routers.adminLogin import adminLogin
from app.src.routers.homeView import home as home_bp
from app.src.routers.logout import logout_bp
from app.src.routers.analitico import analitico_bp
from app.src.routers.pesquisa import pesquisa_bp
from app.src.routers.comunicados import comunicados_bp
from app.src.routers.novo_colaborador import novo_colaborador_bp
from app.src.routers.novo_comunicado import novo_comunicado_bp
from app.src.routers.admin_feriados import admin_feriados_bp
from app.src.routers.beneficios import beneficios_bp
from app.src.routers.auth import auth_bp
from app.src.routers.pesquisas_lista import pesquisas_lista_bp
from app.src.routers.admin_surveys import admin_surveys_bp

def create_app():
    # --- CRIAÇÃO DA APLICAÇÃO ---
    # A app principal agora é responsável por servir os arquivos estáticos da pasta 'assets'
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder='assets',
        static_url_path='/static'
    )

    # --- CONFIGURAÇÃO CENTRALIZADA ---
    is_production = os.getenv('RENDER', False)
    db_path = os.path.join('/var/data', 'pesquisa.db') if is_production else os.path.join(app.instance_path, 'pesquisa.db')

    app.config.from_mapping(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev_key_super_secreta'),
        DATABASE=db_path,
        UPLOAD_FOLDER=os.path.join(project_root, 'app', 'src', 'uploads'),
        SEND_FILE_MAX_AGE_DEFAULT=31536000
    )

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- INICIALIZAÇÃO DE EXTENSÕES ---
    from app.src.config import db
    db.init_app(app)

    # --- LÓGICA DA APLICAÇÃO ---
    app.permanent_session_lifetime = timedelta(minutes=30)

    @app.before_request
    def require_login():
        session.permanent = True
        # Agora só precisamos permitir o endpoint 'static' padrão
        allowed_endpoints = ['auth.login', 'static']
        if 'colaborador_id' not in session and request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth.login'))

    def nl2br(value):
        return Markup(escape(value).replace('\n', '<br>\n'))
    app.jinja_env.filters['nl2br'] = nl2br

    # --- REGISTRO DOS BLUEPRINTS ---
    # O views_bp foi removido para eliminar o conflito
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

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app
