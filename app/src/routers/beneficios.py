from flask import Blueprint, render_template

# Se você usar controle de sessão (ex: @login_required para verificar se o usuário está logado),
# você precisará importá-lo aqui. Exemplo:
# from flask_login import login_required


# 1. Criação do Blueprint
# O primeiro argumento ('beneficios') é o nome interno do blueprint.
# O segundo argumento (__name__) é padrão e ajuda o Flask a localizar recursos.
beneficios_bp = Blueprint(
    'beneficios',
    __name__
)


# 2. Definição da Rota
# Esta rota será acessível em "http://seu-site.com/beneficios"
@beneficios_bp.route('/beneficios')
# @login_required  # Descomente esta linha se a página de benefícios exigir login
def beneficios_page():
    """
    Esta função (view) é executada quando um usuário acessa a URL /beneficios.
    Ela renderiza e retorna o arquivo HTML da página de benefícios.
    """

    # Futuramente, você pode buscar dados do banco de dados aqui
    # e passá-los para o template.
    # Ex: lista_de_beneficios = Beneficio.query.all()
    # return render_template('beneficios/beneficios.html', beneficios=lista_de_beneficios)

    # <<< ALTERAÇÃO AQUI >>>
    # Corrigido para apontar para o template dentro da subpasta 'beneficios'.
    return render_template('beneficios/beneficios.html')