# src/routers/pesquisa.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection

pesquisa_bp = Blueprint('pesquisa', __name__, url_prefix='')

@pesquisa_bp.route('/pesquisa', methods=['GET', 'POST'])
def pesquisa_view():
    # 1) Só permite quem está logado
    user_id = session.get('user_id')
    if not user_id:
        flash('Faça home antes de responder à pesquisa.', 'warning')
        return redirect(url_for('home.login_view'))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 2) Verifica se colaborador existe e se já respondeu
    cursor.execute('SELECT respondeu FROM colaboradores WHERE id = %s', (user_id,))
    colaborador = cursor.fetchone()
    if not colaborador:
        conn.close()
        flash('Usuário não encontrado.', 'danger')
        session.pop('user_id', None)
        return redirect(url_for('home.login_view'))
    if colaborador['respondeu']:
        conn.close()
        flash('Você já respondeu à pesquisa.', 'warning')
        session.pop('user_id', None)
        return redirect(url_for('home.login_view'))

    # 3) Busca o survey ativo
    cursor.execute(
        'SELECT id FROM surveys WHERE name = %s',
        ('Pesquisa de Clima Organizacional',)
    )
    survey = cursor.fetchone()
    if not survey:
        conn.close()
        flash('Pesquisa não cadastrada no sistema.', 'danger')
        return redirect(url_for('home.login_view'))
    survey_id = survey['id']

    # 4) Carrega perguntas + seção + tipo
    cursor.execute("""
      SELECT id, section_title, question_text, question_type
        FROM form_questions
       WHERE survey_id = %s
       ORDER BY order_index
    """, (survey_id,))
    questions = cursor.fetchall()

    # 5) Carrega opções para cada pergunta
    options = {}
    for q in questions:
        cursor.execute("""
          SELECT option_label, option_value
            FROM form_options
           WHERE question_id = %s
           ORDER BY option_label
        """, (q['id'],))
        options[q['id']] = cursor.fetchall()

    if request.method == 'POST':
        # 6) Insere master em responses
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO responses (survey_id) VALUES (%s)',
            (survey_id,)
        )
        response_id = cur.lastrowid

        # 7) Insere cada resposta
        for q in questions:
            ans = request.form.get(f'resposta{q["id"]}', '').strip() or None
            cur.execute(
                'INSERT INTO response_answers (response_id, question_id, answer) '
                'VALUES (%s, %s, %s)',
                (response_id, q['id'], ans)
            )

        # 8) Marca colaborador como respondeu
        cur.execute(
            'UPDATE colaboradores SET respondeu = 1 WHERE id = %s',
            (user_id,)
        )

        conn.commit()
        conn.close()
        flash('Obrigado por responder à pesquisa!', 'success')
        session.pop('user_id', None)
        return redirect(url_for('home.login_view'))

    # GET: renderiza o formulário com perguntas e opções do banco
    conn.close()
    return render_template(
        'pesquisa/pesquisa.html',
        questions=questions,
        options=options
    )
