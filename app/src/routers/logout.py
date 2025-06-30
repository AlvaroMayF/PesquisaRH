# src/routers/logout.py
from flask import Blueprint, session, redirect, url_for

# Blueprint para logout de usuários
logout = Blueprint('logout', __name__)


@logout.route('/logout')
def logout_view():
    """
    Finaliza a sessão do usuário e redireciona para a página inicial.
    """
    # session.clear() é eficaz e remove todas as chaves da sessão.
    session.clear()

    # CORREÇÃO: Redireciona para a página inicial correta.
    return redirect(url_for('home.home_view'))
