import os
from flask import Flask, send_from_directory, Blueprint, session, redirect, url_for, request
from markupsafe import escape, Markup  # Mantenha ambas as importações
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
    static_dir = os.path.join(base, 'assets')

    # Ajuste para a pasta de uploads de curriculos que está dentro de src/app/uploads/curriculos
    upload_root_dir = os.path.join(base, 'uploads')
    os.makedirs(os.path.join(upload_root_dir, 'curriculos'), exist_ok=True)

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    app.config['UPLOAD_FOLDER'] = upload_root_dir

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

    # --- FUNÇÃO NL2BR COM DEBUG E LÓGICA REFINADA PARA O TESTE ---
    def nl2br(value):
        """Converte quebras de linha em texto para tags <br> em HTML.
           Adicionado debug para investigar o problema de <br> literal."""

        # Converte para string e padroniza quebras de linha para '\n'
        cleaned_value = str(value).replace('\r\n', '\n').replace('\r', '\n')
        print(f"DEBUG NL2BR: Valor de entrada (repr): {repr(cleaned_value)}")

        # Primeiro, escape todo o HTML para evitar XSS
        # Se 'value' já contiver '&lt;br&gt;' ou '<br>', 'escape' vai re-escapar ou deixar como está.
        escaped_value = escape(cleaned_value)

        # Agora, substitua as quebras de linha (que são '\n' após a limpeza) por tags <br>
        # O Markup('<br>\n') garante que '<br>' seja injetado como HTML e não escapado novamente.
        final_html = escaped_value.replace('\n', Markup('<br>\n'))

        return final_html  # Retorna um objeto Markup, que é 'safe' por padrão

    app.jinja_env.filters['nl2br'] = nl2br
    # --- FIM DA FUNÇÃO NL2BR ---

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