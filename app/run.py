import os
from flask import Flask, send_from_directory, Blueprint, session, redirect, url_for, request
from markupsafe import escape, Markup
from datetime import timedelta

# ----------------------------------------------------------------------
# Blueprint “views” para servir templates estáticos (CSS, HTML, etc)
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
    base = os.path.abspath(os.path.dirname(__file__))

    # Diretórios de templates e estáticos
    template_dir = os.path.join(base, 'src', 'views')
    static_dir = os.path.join(base, 'assets')  # A pasta 'assets' é servida como '/static'

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    # ======================================================================
    #                 CONFIGURAÇÃO DE PASTAS DE UPLOAD
    # ======================================================================

    # --- Configuração do diretório de upload para currículos ---
    upload_root_dir = os.path.join(base, 'uploads')
    os.makedirs(os.path.join(upload_root_dir, 'curriculos'), exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_root_dir

    # --- Configuração dos diretórios de upload para comunicados ---
    upload_images_dir = os.path.join(static_dir, 'uploads', 'images')
    upload_videos_dir = os.path.join(static_dir, 'uploads', 'videos')
    os.makedirs(upload_images_dir, exist_ok=True)
    os.makedirs(upload_videos_dir, exist_ok=True)
    app.config['UPLOAD_FOLDER_IMAGES'] = upload_images_dir
    app.config['UPLOAD_FOLDER_VIDEOS'] = upload_videos_dir

    # --- Configuração do diretório para FOTOS DE COLABORADORES ---
    fotos_dir = os.path.join(static_dir, 'uploads', 'fotos_colaboradores')
    os.makedirs(fotos_dir, exist_ok=True)
    app.config['FOTOS_FOLDER'] = fotos_dir

    # ======================================================================
    #           CONFIGURAÇÃO DA INTEGRAÇÃO CONTROL ID
    # ======================================================================

    # --- Credenciais para a API de Sincronização ---
    app.config['IDSECURE_IP'] = '10.0.1.0:30443'
    app.config['IDSECURE_USER'] = 'admin'
    app.config['IDSECURE_PASSWORD'] = 'admin123'

    # --- Credenciais para o BANCO DE DADOS do iDSecure ---
    app.config['IDSECURE_DB_HOST'] = '10.0.1.0'
    app.config['IDSECURE_DB_USER'] = 'integracao'
    app.config['IDSECURE_DB_PASSWORD'] = '[]-@samar@hsp'
    app.config['IDSECURE_DB_NAME'] = 'acesso'
    app.config['IDSECURE_DB_PORT'] = 3306

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

    app.register_blueprint(views_bp)

    # Registra todos os blueprints de rota
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

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/admin/admin.css')
    def admin_css():
        return send_from_directory(
            os.path.join(template_dir, 'admin'),
            'admin.css'
        )

    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_em_producao')

    return app


# Instância para execução direta
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(debug=True, port=port)