# src/routers/pesquisa.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection

pesquisa_bp = Blueprint('pesquisa', __name__, url_prefix='')

@pesquisa_bp.route('/pesquisa', methods=['GET', 'POST'])
def pesquisa_view():
    # 1) Só permite quem está logado
    user_id = session.get('user_id')
    if not user_id:
        flash('Faça login antes de responder à pesquisa.', 'warning')
        return redirect(url_for('login.login_view'))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 2) Verifica se colaborador existe e se já respondeu
    cursor.execute('SELECT respondeu FROM colaboradores WHERE id = %s', (user_id,))
    colaborador = cursor.fetchone()
    if not colaborador:
        conn.close()
        flash('Usuário não encontrado.', 'danger')
        session.pop('user_id', None)
        return redirect(url_for('login.login_view'))

    if colaborador['respondeu']:
        conn.close()
        flash('Você já respondeu à pesquisa.', 'warning')
        session.pop('user_id', None)
        return redirect(url_for('login.login_view'))

    # 3) Identifica survey ativo (por nome ou flag)
    cursor.execute(
        'SELECT id FROM surveys WHERE name = %s',
        ('Pesquisa de Clima Organizacional',)
    )
    survey = cursor.fetchone()
    if not survey:
        conn.close()
        flash('Pesquisa não cadastrada no sistema.', 'danger')
        return redirect(url_for('login.login_view'))
    survey_id = survey['id']

    # 4) Carrega todas as perguntas desse survey
    cursor.execute(
        'SELECT id FROM form_questions WHERE survey_id = %s ORDER BY id',
        (survey_id,)
    )
    questions = cursor.fetchall()
    question_ids = [q['id'] for q in questions]

    if request.method == 'POST':
        # inicia transação
        cur = conn.cursor()

        # 5) Insere o master record em responses (sem cpf!)
        cur.execute(
            'INSERT INTO responses (survey_id) VALUES (%s)',
            (survey_id,)
        )
        response_id = cur.lastrowid

        # 6) Insere cada resposta detalhada
        for qid in question_ids:
            answer = request.form.get(f'resposta{qid}', '').strip() or None
            cur.execute(
                'INSERT INTO response_answers (response_id, question_id, answer) '
                'VALUES (%s, %s, %s)',
                (response_id, qid, answer)
            )

        # 7) Marca colaborador como “já respondeu”
        cur.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = %s',
            (user_id,)
        )

        # finaliza
        conn.commit()
        conn.close()

        flash('Obrigado por responder à pesquisa!', 'success')
        session.pop('user_id', None)
        return redirect(url_for('login.login_view'))

    # GET: apenas renderiza
    conn.close()
    return render_template('pesquisa/pesquisa.html')
