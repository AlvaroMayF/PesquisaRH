# app/src/routers/pesquisaLogin.py

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from src.config.db import get_db_connection

pesquisa_login = Blueprint('pesquisa_login', __name__, url_prefix='/pesquisa')

@pesquisa_login.route('/', methods=['GET', 'POST'])
def login_pesquisa_view():
    """
    Exibe o formulário de login da pesquisa (GET)
    e processa o POST de CPF + data de nascimento.
    Só segue para a pesquisa se o colaborador existir e
    não tiver respondido ainda.
    """
    error = None

    if request.method == 'POST':
        raw_cpf  = request.form.get('cpf', '').strip()
        raw_date = request.form.get('data_nascimento', '').strip()

        # 1) Extrai apenas dígitos e garante 11 caracteres
        digits = ''.join(filter(str.isdigit, raw_cpf))
        cpf    = digits.zfill(11)
        if len(cpf) != 11:
            error = 'CPF inválido. Deve conter 11 dígitos.'
            return render_template('LoginPesquisa/LoginPesquisa.html', error=error)

        # 2) Converte a string de data para objeto date
        try:
            if '/' in raw_date:
                data_nasc = datetime.strptime(raw_date, '%d/%m/%Y').date()
            else:
                data_nasc = datetime.fromisoformat(raw_date).date()
        except ValueError:
            error = 'Data inválida. Use DD/MM/AAAA ou selecione pelo calendário.'
            return render_template('LoginPesquisa/LoginPesquisa.html', error=error)

        # 3) Consulta no banco
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, respondeu '
            'FROM colaboradores '
            'WHERE cpf = %s AND data_nascimento = %s',
            (cpf, data_nasc)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # 4) Validações finais
        if not user:
            error = 'Dados não encontrados.'
        elif user['respondeu']:
            error = 'Você já respondeu à pesquisa.'
        else:
            session['user_id'] = user['id']
            # Redireciona para o blueprint de pesquisa propriamente dito
            return redirect(url_for('pesquisa.pesquisa_view'))

    # GET ou POST com erro
    return render_template('LoginPesquisa/LoginPesquisa.html', error=error)
