import os
from flask import Flask, send_from_directory, Blueprint
from markupsafe import escape, Markup

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
from src.routers.logout import logout
from src.routers.analitico import analitico
from src.routers.pesquisaLogin import pesquisa_login
from src.routers.pesquisa import pesquisa_bp
from src.routers.comunicados import comunicados_bp
from src.routers.novo_colaborador import novo_colaborador_bp
from src.routers.novo_comunicado import novo_comunicado_bp
from src.routers.admin_feriados import admin_feriados_bp
from src.routers.beneficios import beneficios_bp  # <<< NOVA LINHA


# ----------------------------------------------------------------------
# Factory para criar e configurar a aplicação
# ----------------------------------------------------------------------
def create_app():
    base = os.path.abspath(os.path.dirname(__file__))

    # Diretórios de templates e estáticos
    template_dir = os.path.join(base, 'src', 'views')
    static_dir = os.path.join(base, 'assets')
    upload_dir = os.path.join(base, 'src', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)  # Cria a pasta se não existir

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    app.config['UPLOAD_FOLDER'] = upload_dir

    # Função e registo do filtro nl2br para formatar texto nos templates
    def nl2br(value):
        """Converte quebras de linha em texto para tags <br> em HTML."""
        return Markup(escape(value).replace('\n', '<br>\n'))

    app.jinja_env.filters['nl2br'] = nl2br

    # Configura cache para assets estáticos (1 ano)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Tenta habilitar compressão Gzip/Brotli
    try:
        from flask_compress import Compress
        Compress(app)
    except ImportError:
        pass

    # Serve conteúdo de src/views em /views_static
    app.register_blueprint(views_bp)

    # Registra todos os blueprints de rota
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(adminLogin)
    app.register_blueprint(home_bp)
    app.register_blueprint(logout)
    app.register_blueprint(analitico)
    app.register_blueprint(pesquisa_login)
    app.register_blueprint(pesquisa_bp)
    app.register_blueprint(comunicados_bp)
    app.register_blueprint(novo_colaborador_bp)
    app.register_blueprint(novo_comunicado_bp)
    app.register_blueprint(admin_feriados_bp)
    app.register_blueprint(beneficios_bp)  # <<< NOVA LINHA

    # Nova rota para servir as imagens enviadas
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Rota para servir admin.css de /views/admin/
    @app.route('/admin/admin.css')
    def admin_css():
        return send_from_directory(
            os.path.join(template_dir, 'admin'),
            'admin.css'
        )

    # Chave de sessão
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_em_producao')

    return app


# Instância para execução direta
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(debug=True, port=port)