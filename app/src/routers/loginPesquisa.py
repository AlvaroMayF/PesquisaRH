# src/routers/loginPesquisa.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from src.config.db import get_db_connection

# Blueprint para o login da pesquisa
login = Blueprint('login', __name__, url_prefix='')

@login.route('/', methods=['GET', 'POST'])
def login_view():
    """
    Exibe o formulário de login (GET) e processa o envio (POST).
    """
    error = None

    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        data_nascimento = request.form.get('data_nascimento', '').strip()

        # Validação básica de CPF
        if not cpf.isdigit():
            error = 'Use somente números no campo CPF.'
            return render_template('login/login.html', error=error)

        conn = get_db_connection()
        user = conn.execute(
            'SELECT id, respondeu FROM colaboradores '
            'WHERE cpf = ? AND data_nascimento = ?',
            (cpf, data_nascimento)
        ).fetchone()
        conn.close()

        if not user:
            error = 'Dados inválidos.'
        elif user['respondeu']:
            error = 'Você já respondeu à pesquisa e não pode entrar novamente.'
        else:
            # Grava o ID do usuário na sessão e redireciona
            session['user_id'] = user['id']
            # Agora apontamos para o endpoint correto do blueprint de pesquisa
            return redirect(url_for('pesquisa.pesquisa_view'))

    # GET ou POST com erro: renderiza a página de login
    return render_template('login/login.html', error=error)
