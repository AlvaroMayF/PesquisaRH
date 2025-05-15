# app/app.py

import os
from flask import Flask, Blueprint

# -----------------------------------------------------------------------------
# Blueprint “views” para servir TODOS os arquivos sob app/src/views como estático
# -----------------------------------------------------------------------------
views_bp = Blueprint(
    'views',
    __name__,
    static_folder='src/views',
    static_url_path='/views_static'  # ficará disponível em /views_static/...
)

# -----------------------------------------------------------------------------
# Importação dos seus Blueprints de rota
# -----------------------------------------------------------------------------
from src.routers.admin         import admin
from src.routers.adminLogin    import adminLogin
from src.routers.loginPesquisa import login
from src.routers.logout        import logout
from src.routers.analitico     import analitico
from src.routers.pesquisa      import pesquisa_bp as pesquisa

# -----------------------------------------------------------------------------
# Factory para criar e configurar a aplicação
# -----------------------------------------------------------------------------
def create_app():
    # Pasta raiz onde está este arquivo (app/)
    root = os.path.abspath(os.path.dirname(__file__))

    # Diretório de templates Jinja2
    template_dir = os.path.join(root, 'src', 'views')
    # Diretório de assets (CSS global, imagens) servido em /static
    static_dir   = os.path.join(root, 'assets')

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    # Registra primeiro o blueprint de views para servir src/views estáticos
    app.register_blueprint(views_bp)

    # Registra em seguida todos os seus blueprints de rota
    app.register_blueprint(admin)       # /admin
    app.register_blueprint(adminLogin)  # /admin-login
    app.register_blueprint(login)       # /
    app.register_blueprint(logout)      # /logout
    app.register_blueprint(analitico)   # /analitico
    app.register_blueprint(pesquisa)    # /pesquisa

    # Chave secreta para sessões (troque em produção)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'troque_em_producao')

    return app

# Instância da aplicação
app = create_app()

if __name__ == '__main__':
    # Usa porta 10000 ou a definida na variável de ambiente PORT
    port = int(os.getenv('PORT', 10000))
    app.run(debug=True, port=port)
