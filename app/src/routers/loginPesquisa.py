# app/src/routers/loginPesquisa.py

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session
from src.config.db import get_db_connection

# Definição do Blueprint de login (rota raiz '/')
login = Blueprint('login', __name__, url_prefix='')

@login.route('/', methods=['GET', 'POST'])
def login_view():
    """
    Exibe o formulário de login (GET) e processa o POST de CPF + data de nascimento.
    """
    error = None

    if request.method == 'POST':
        raw_cpf  = request.form.get('cpf', '').strip()
        raw_date = request.form.get('data_nascimento', '').strip()

        # 1) Extrai apenas dígitos e garante exatamente 11 caracteres (zero-padding à esquerda)
        digits = ''.join(filter(str.isdigit, raw_cpf))
        cpf    = digits.zfill(11)
        if len(cpf) != 11:
            error = 'CPF inválido. Deve conter 11 dígitos.'
            return render_template('login/login.html', error=error)

        # 2) Converte a string de data para objeto date
        try:
            if '/' in raw_date:
                # Formato DD/MM/AAAA
                data_nascimento = datetime.strptime(raw_date, '%d/%m/%Y').date()
            else:
                # Formato ISO YYYY-MM-DD (quando usado <input type="date">)
                data_nascimento = datetime.fromisoformat(raw_date).date()
        except ValueError:
            error = 'Data inválida. Use DD/MM/AAAA ou selecione pelo calendário.'
            return render_template('login/login.html', error=error)

        # 3) Consulta no banco
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, respondeu '
            'FROM colaboradores '
            'WHERE cpf = %s AND data_nascimento = %s',
            (cpf, data_nascimento)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # 4) Lógica de sucesso/erro
        if not user:
            error = 'Dados inválidos.'
        elif user['respondeu']:
            error = 'Você já respondeu à pesquisa e não pode entrar novamente.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('pesquisa.pesquisa_view'))

    # Renderiza o template de login (GET ou POST com erro)
    return render_template('login/login.html', error=error)
