from flask import Blueprint, render_template, request, redirect, url_for, session
from ..config.db import get_db_connection

# Blueprint para o login do administrador
adminLogin = Blueprint('adminLogin', __name__)

@adminLogin.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    Exibe o formulário de login de administrador (GET) e processa o login (POST).
    """
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM admins WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['admin_logged_in'] = True
            # Redireciona para a área principal do admin (ajuste o endpoint conforme admin.py)
            return redirect(url_for('admin.admin'))
        else:
            error = 'Usuário ou senha incorretos.'

    # Renderiza a página de login (GET ou falha de login)
    return render_template('adminLogin/adminLogin.html', error=error)
