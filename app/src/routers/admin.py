# src/routers/admin.py

from flask import Blueprint, render_template, redirect, url_for, session
from ..config.db import get_db_connection
# Cria o blueprint para as rotas de administração
admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/', methods=['GET'])
def dashboard():
    """
    Painel principal do administrador.
    Só acessível se a sessão 'admin_logged_in' estiver definida.
    """
    # Se não estiver logado, manda para o formulário de home
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))
    # Renderiza o template em app/views/admin/admin.html
    return render_template('admin/admin.html')
