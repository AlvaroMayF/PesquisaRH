# app/run.py

import os
from flask import Flask, send_from_directory, Blueprint, session, redirect, url_for, request
from markupsafe import escape, Markup
from datetime import timedelta
from dotenv import load_dotenv

# --- CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE ---
base_dir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=dotenv_path)

# ----------------------------------------------------------------------
# Blueprint “views” para servir templates estáticos
# ----------------------------------------------------------------------
views_bp = Blueprint(
    'views',
    __name__,
    static_folder='src/views',
    static_url_path='/views_static'
)

# ----------------------------------------------------------------------
# Import dos blueprints de rota
# ----------------------------------------------------------------------
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
from src.routers.carreiras import carreiras_bp
from src.routers.admin_vagas import admin_vagas_bp
from src.routers.admin_candidaturas import admin_candidaturas_bp

# ----------------------------------------------------------------------
# Factory para criar e configurar a aplicação
# ----------------------------------------------------------------------
def create_app():
    template_dir = os.path.join(base_dir, 'src', 'views')
    static_dir = os.path.join(base_dir, 'assets')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    # ======================================================================
    #                 CONFIGURAÇÃO CENTRALIZADA (Lida do .env)
    # ======================================================================

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-padrao-muito-segura')

    # --- Configurações da Integração Control iD ---
    app.config['IDSECURE_DB_HOST'] = os.getenv('IDSECURE_DB_HOST')
    app.config['IDSECURE_DB_USER'] = os.getenv('IDSECURE_DB_USER')
    app.config['IDSECURE_DB_PASSWORD'] = os.getenv('IDSECURE_DB_PASSWORD')
    app.config['IDSECURE_DB_NAME'] = os.getenv('IDSECURE_DB_NAME')
    app.config['IDSECURE_DB_PORT'] = os.getenv('IDSECURE_DB_PORT')

    app.config['IDSECURE_IMAGES_SHARE_PATH'] = os.getenv('IDSECURE_IMAGES_SHARE_PATH')

    app.config['IDSECURE_SHARE_USER'] = os.getenv('IDSECURE_SHARE_USER')
    app.config['IDSECURE_SHARE_PASSWORD'] = os.getenv('IDSECURE_SHARE_PASSWORD')

    # --- CORREÇÃO: Carrega as credenciais da API iDSecure ---
    app.config['IDSECURE_BASE_URL'] = os.getenv('IDSECURE_BASE_URL')
    app.config['IDSECURE_API_USER'] = os.getenv('IDSECURE_API_USER')
    app.config['IDSECURE_API_PASSWORD'] = os.getenv('IDSECURE_API_PASSWORD')

    # --- Configuração de Pastas de Upload ---
    default_fotos_dir = os.path.join(base_dir, 'uploads', 'fotos_colaboradores')
    app.config['FOTOS_FOLDER'] = os.getenv('FOTOS_FOLDER', default_fotos_dir)
    os.makedirs(app.config['FOTOS_FOLDER'], exist_ok=True)

    # ======================================================================
    #           O RESTANTE DA CONFIGURAÇÃO DA APLICAÇÃO
    # ======================================================================

    app.permanent_session_lifetime = timedelta(minutes=15)

    @app.before_request
    def require_login():
        session.permanent = True
        allowed_endpoints = ['auth.login', 'static', 'views.static', 'carreiras.index', 'adminLogin.admin_login']
        is_admin_route = request.path.startswith('/admin/')
        if 'colaborador_id' not in session and not is_admin_route and request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth.login'))
        if is_admin_route and not session.get('admin_logged_in') and request.endpoint not in allowed_endpoints:
            return redirect(url_for('adminLogin.admin_login'))

    def nl2br(value):
        cleaned_value = str(value).replace('\r\n', '\n').replace('\r', '\n')
        escaped_value = escape(cleaned_value)
        final_html = escaped_value.replace('\n', Markup('<br>\n'))
        return final_html

    app.jinja_env.filters['nl2br'] = nl2br
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    try:
        from flask_compress import Compress
        Compress(app)
    except ImportError:
        pass

    # Registra todos os seus blueprints
    app.register_blueprint(views_bp)
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
    app.register_blueprint(carreiras_bp)
    app.register_blueprint(admin_vagas_bp)
    app.register_blueprint(admin_candidaturas_bp)

    print("✅ Aplicação Flask criada e configurada com sucesso!")
    return app


# Instância para execução
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(debug=True, host='0.0.0.0', port=port)