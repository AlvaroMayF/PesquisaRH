from flask import Blueprint, render_template

# 1. Criação do Blueprint.
# O primeiro argumento 'comunicados' será o prefixo do endpoint.
comunicados_bp = Blueprint('comunicados', __name__)

# 2. Definição da rota '/comunicados'
@comunicados_bp.route('/comunicados')
def view_comunicados():
    """
    Esta função será executada quando um usuário acessar a URL /comunicados
    e irá renderizar o template HTML correspondente.
    """
    # O Flask já sabe que a pasta de templates é 'app/src/views',
    # então o caminho aqui é relativo a ela.
    return render_template('comunicados/comunicados.html')