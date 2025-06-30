from flask import Blueprint, render_template, session, redirect, url_for

# Nome do blueprint
admin = Blueprint('admin', __name__)

# CORREÇÃO: A rota foi alterada de '/admin' para '/admin/'.
# A barra no final é a forma padrão para URLs que representam um "diretório".
@admin.route('/admin/', methods=['GET'])
def admin_panel():
    """
    Exibe o painel de administração.
    Verifica se o usuário tem uma sessão de admin ativa antes de mostrar a página.
    """
    # Verifica se o administrador está logado
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        # Se não estiver logado, redireciona para a página de login
        return redirect(url_for('adminLogin.admin_login'))

    # Se estiver logado, mostra o painel do administrador
    username = session.get('username', 'Admin')
    return render_template('admin/admin.html', username=username)

# Você pode adicionar outras rotas do painel de admin aqui abaixo
# Ex: @admin.route('/usuarios') -> acessível em /admin/usuarios
#     def gerenciar_usuarios():
#         ...
