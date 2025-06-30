# app/src/routers/adminLogin.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection

# Blueprint para o login do administrador.
adminLogin = Blueprint('adminLogin', __name__)


@adminLogin.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    Exibe o formulário de login de administrador (GET) e processa o login (POST).
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

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
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']
            session['username'] = user['username']

            # Redireciona para o painel de admin.
            # Certifique-se de que a rota em admin.py se chama 'admin_panel'.
            return redirect(url_for('admin.admin_panel'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
            return redirect(url_for('adminLogin.admin_login'))

    # CORREÇÃO DEFINITIVA: O caminho e o nome do ficheiro foram ajustados
    # para corresponder exatamente à sua estrutura de projeto.
    return render_template('adminLogin/adminLogin.html')
