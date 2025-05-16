# app/app.py

import os
from flask import Flask, Blueprint

# ----------------------------------------------------------------------
# Blueprint “views” para servir os seus templates estáticos (CSS, HTML, etc)
# localizados em app/src/views via a URL /views_static/...
# ----------------------------------------------------------------------
views_bp = Blueprint(
    'views',
    __name__,
    static_folder='src/views',
    static_url_path='/views_static'
)

# ----------------------------------------------------------------------
# Import dos seus blueprints de rota
# ----------------------------------------------------------------------
from src.routers.admin         import admin           # /admin
from src.routers.adminLogin    import adminLogin      # /admin-login
from src.routers.loginPesquisa import login           # /
from src.routers.logout        import logout          # /logout
from src.routers.analitico     import analitico       # /analitico
from src.routers.pesquisa      import pesquisa_bp     # /pesquisa

# ----------------------------------------------------------------------
# Factory para criar e configurar a aplicação
# ----------------------------------------------------------------------
def create_app():
    base = os.path.abspath(os.path.dirname(__file__))

    # Onde estão seus templates Jinja2 (HTML)
    template_dir = os.path.join(base, 'src', 'views')
    # Onde ficam seus arquivos estáticos principais (CSS globais, imagens, JS)
    static_dir   = os.path.join(base, 'assets')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    # Serve tudo que estiver em src/views como “/views_static/...”
    app.register_blueprint(views_bp)

    # Registra todos os seus blueprints de rota
    app.register_blueprint(admin)        # Dashboard Admin → /admin
    app.register_blueprint(adminLogin)   # Login Admin     → /admin-login
    app.register_blueprint(login)        # Login Colaborador → /
    app.register_blueprint(logout)       # Logout → /logout
    app.register_blueprint(analitico)    # Visão Analítica → /analitico
    app.register_blueprint(pesquisa_bp)  # Pesquisa → /pesquisa

    # Chave para sessão; troque em produção por algo secreto
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_em_producao')

    return app

# Cria uma instância de app para rodar diretamente
app = create_app()

if __name__ == '__main__':
    # Porta 10000 ou a que estiver em PORT no .env
    port = int(os.getenv('PORT', 10000))
    app.run(debug=True, port=port)
