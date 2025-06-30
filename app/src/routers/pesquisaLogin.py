# app/src/routers/pesquisaLogin.py

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from ..config.db import get_db_connection

pesquisa_login = Blueprint('pesquisa_login', __name__, url_prefix='/pesquisa')


@pesquisa_login.route('/', methods=['GET', 'POST'])
def login_pesquisa_view():
    error = None

    if request.method == 'POST':
        raw_cpf = request.form.get('cpf', '').strip()
        raw_date = request.form.get('data_nascimento', '').strip()

        # 1) Lógica de CPF restaurada para o padrão de 11 dígitos
        digits = ''.join(filter(str.isdigit, raw_cpf))

        # Garante que o CPF tenha 11 dígitos, preenchendo com zeros se necessário
        cpf = digits.zfill(11)

        # Validação de 11 dígitos reativada
        if len(cpf) != 11:
            error = 'CPF inválido. Deve conter 11 dígitos.'
            return render_template('LoginPesquisa/LoginPesquisa.html', error=error)

        try:
            data_nasc = datetime.fromisoformat(raw_date).date()
        except (ValueError, TypeError):
            error = 'Data inválida. Use o calendário para selecionar.'
            return render_template('LoginPesquisa/LoginPesquisa.html', error=error)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, respondeu FROM colaboradores WHERE cpf = %s AND data_nascimento = %s',
            (cpf, data_nasc)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            error = 'Dados não encontrados.'
        elif user['respondeu']:
            error = 'Você já respondeu à pesquisa.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('pesquisa.pesquisa_view'))

    return render_template('LoginPesquisa/LoginPesquisa.html', error=error)