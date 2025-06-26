# src/routers/logout.py
from flask import Blueprint, session, redirect, url_for
# Blueprint para logout de usuários
logout = Blueprint('logout', __name__, url_prefix='')
@logout.route('/logout')
def logout_view():
    """
    Finaliza a sessão do usuário e redireciona para a página de home.
    """
    session.clear()
    # Redireciona para o endpoint de home do blueprint 'home'
    return redirect(url_for('home.login_view'))
