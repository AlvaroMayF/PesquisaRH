# Arquivo: src/utils/decorators.py

from functools import wraps
from flask import session, redirect, url_for, flash


def admin_required(f):
    """
    Este decorator verifica se o usuário está logado e tem a permissão 'admin'.
    Se não tiver, ele redireciona para a página inicial com uma mensagem de erro.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se o usuário está logado E se o seu perfil é 'admin'
        if not session.get('admin_logged_in') or session.get('admin_role') != 'admin':
            flash('Você não tem permissão para acessar esta página.', 'error')
            # Redireciona para a página de login de admin, ou para a 'home' se preferir.
            return redirect(url_for('adminLogin.admin_login'))

        # Se a verificação passar, executa a rota original
        return f(*args, **kwargs)

    return decorated_function