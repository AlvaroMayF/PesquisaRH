# app/src/routers/adminLogin.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection
from werkzeug.security import check_password_hash

# Para segurança máxima em produção, considere usar hash de senhas.
# from werkzeug.security import check_password_hash

adminLogin = Blueprint('adminLogin', __name__)


@adminLogin.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """
    Exibe o formulário de login (GET) e processa a autenticação (POST),
    armazenando o perfil ('role') do usuário na sessão.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = None  # Garante que a variável exista fora do bloco try
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Uma única consulta ao banco de dados para buscar o usuário.
            # A verificação da senha será feita em Python.
            cursor.execute('SELECT id, username, password, role FROM admins WHERE username = %s', (username,))
            user = cursor.fetchone()

        except Exception as e:
            # Captura qualquer erro de banco de dados
            flash('Erro ao conectar ao serviço de autenticação.', 'error')
            print(f"Erro no banco durante login: {e}")
            return redirect(url_for('adminLogin.admin_login'))
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

        # Validação da Senha
        # A sua lógica atual de comparação de texto simples é mantida, conforme solicitado.
        # O ideal seria: if user and check_password_hash(user['password'], password):
        if user and check_password_hash(user['password'], password):
            # Se o usuário e a senha corresponderem, armazena os dados na sessão.
            session['admin_logged_in'] = True
            session['admin_id'] = user['id']
            session['username'] = user['username']

            # <<< Ponto Chave: Armazenamos o perfil ('role') na sessão >>>
            session['admin_role'] = user['role']

            print(f"SUCESSO: Login do usuário '{user['username']}' com perfil '{user['role']}'.")
            return redirect(url_for('admin.admin_panel'))
        else:
            # Se o usuário não existir ou a senha estiver incorreta
            flash('Usuário ou senha incorretos.', 'error')
            return redirect(url_for('adminLogin.admin_login'))

    # Para requisições GET, apenas exibe a página de login
    return render_template('adminLogin/adminLogin.html')