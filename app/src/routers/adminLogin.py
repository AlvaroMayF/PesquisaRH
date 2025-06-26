# app/src/routers/adminLogin.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from ..config.db import get_db_connection

# Blueprint para o home do administrador
adminLogin = Blueprint('adminLogin', __name__, url_prefix='/admin-home')

@adminLogin.route('/', methods=['GET', 'POST'])
def admin_login():
    """
    Exibe o formulário de home de administrador (GET) e processa o home (POST).
    """
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # 1) Pega um cursor, não chama conn.execute() diretamente
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, username FROM admins WHERE username = %s AND password = %s',
            (username, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # marca sessão de admin
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']

            # 2) Redireciona para o dashboard do admin
            #    Em admin.py o endpoint padrão é 'admin.dashboard'
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Usuário ou senha incorretos.'

    # GET ou POST com erro: renderiza a tela de home de admin
    return render_template('adminLogin/adminLogin.html', error=error)
