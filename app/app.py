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
from src.routers.analitico import analitico
# CORRIGIDO: O nome da variável importada agora é 'pesquisa_bp'
from src.routers.pesquisa import pesquisa_bp
from src.routers.comunicados import comunicados_bp
from src.routers.novo_colaborador import novo_colaborador_bp
from src.routers.novo_comunicado import novo_comunicado_bp
from src.routers.admin_feriados import admin_feriados_bp
from src.routers.beneficios import beneficios_bp
from src.routers.auth import auth_bp
from src.routers.pesquisas_lista import pesquisas_lista_bp
from src.routers.admin_surveys import admin_surveys_bp

# ----------------------------------------------------------------------
# Factory para criar e configurar a aplicação
# ----------------------------------------------------------------------
def create_app():
    base = os.path.abspath(os.path.dirname(__file__))

    # Diretórios de templates e estáticos
    template_dir = os.path.join(base, 'src', 'views')
    static_dir = os.path.join(base, 'assets')
    upload_dir = os.path.join(base, 'src', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    app.config['UPLOAD_FOLDER'] = upload_dir

    app.permanent_session_lifetime = timedelta(minutes=15)

    @app.before_request
    def require_login():
        session.permanent = True

        allowed_endpoints = ['auth.login', 'static', 'views.static']

        if 'colaborador_id' not in session and request.endpoint not in allowed_endpoints:
            return redirect(url_for('auth.login'))

    def nl2br(value):
        """Converte quebras de linha em texto para tags <br> em HTML."""
        return Markup(escape(value).replace('\n', '<br>\n'))

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
    app.register_blueprint(analitico)
    # CORRIGIDO: O nome da variável registrada agora é 'pesquisa_bp'
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
