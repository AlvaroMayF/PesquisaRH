# src/routers/pesquisa.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection
# Define o blueprint para as rotas de pesquisa
pesquisa_bp = Blueprint('pesquisa', __name__, url_prefix='')
@pesquisa_bp.route('/pesquisa', methods=['GET', 'POST'])
def pesquisa_view():
    """
    Exibe o formulário de pesquisa (GET) e processa as respostas (POST).
    """
    user_id = session.get('user_id')
    if not user_id:
        flash('Faça login antes de responder à pesquisa.', 'warning')
        return redirect(url_for('login.login_view'))

    conn = get_db_connection()
    row = conn.execute(
        'SELECT respondeu FROM colaboradores WHERE id = ?',
        (user_id,)
    ).fetchone()

    # Se o usuário já respondeu, limpa sessão e volta ao login
    if row and row['respondeu']:
        conn.close()
        flash('Você já respondeu à pesquisa.', 'warning')
        session.pop('user_id', None)
        return redirect(url_for('login.login_view'))

    if request.method == 'POST':
        cur = conn.cursor()
        # Insere o registro mestre na tabela respostas
        cur.execute('INSERT INTO respostas (data_resposta) VALUES (CURRENT_TIMESTAMP)')
        response_id = cur.lastrowid

        # Insere cada resposta detalhada
        for qid in range(1, 34):
            ans = request.form.get(f'resposta{qid}', '').strip()
            cur.execute(
                'INSERT INTO response_answers (response_id, question_id, answer) '
                'VALUES (?, ?, ?)',
                (response_id, qid, ans)
            )

        # Marca que o colaborador já respondeu
        cur.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = ?',
            (user_id,)
        )

        conn.commit()
        conn.close()

        flash('Obrigado por responder à pesquisa!', 'success')
        session.pop('user_id', None)
        return redirect(url_for('login.login_view'))

    # GET: apenas renderiza o formulário
    conn.close()
    return render_template('pesquisa/pesquisa.html')
