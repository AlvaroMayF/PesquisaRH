# src/routers/analitico.py

from flask import Blueprint, render_template, redirect, url_for, session
from ..config.db import get_db_connection

analitico = Blueprint('analitico', __name__, url_prefix='/analitico')


@analitico.route('/')
def analitico_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # --- ATUALIZAÇÃO DOS INDICADORES ---
    cur.execute("SELECT COUNT(id) AS total_colaboradores FROM colaboradores")
    total_colaboradores = cur.fetchone()['total_colaboradores']

    cur.execute("SELECT COUNT(id) AS pesquisas_respondidas FROM colaboradores WHERE respondeu = 1")
    pesquisas_respondidas = cur.fetchone()['pesquisas_respondidas']

    # Cálculo da taxa de participação
    taxa_participacao = 0
    if total_colaboradores > 0:
        taxa_participacao = round((pesquisas_respondidas / total_colaboradores) * 100)

    indicadores = {
        'total_colaboradores': total_colaboradores,
        'pesquisas_respondidas': pesquisas_respondidas,
        'taxa_participacao': taxa_participacao  # Novo indicador
    }
    # --- FIM DA ATUALIZAÇÃO ---

    cur.execute("SELECT id, question_text, question_type FROM form_questions ORDER BY order_index")
    questions = cur.fetchall()

    cur.execute("SELECT question_id, answer FROM response_answers WHERE answer IS NOT NULL AND answer != ''")
    all_answers = cur.fetchall()
    cur.close()
    conn.close()

    answers_by_qid = {}
    for answer_row in all_answers:
        qid = answer_row['question_id']
        if qid not in answers_by_qid:
            answers_by_qid[qid] = []
        answers_by_qid[qid].append(answer_row['answer'])

    charts = []
    for question in questions:
        qid = question['id']
        answers = answers_by_qid.get(qid, [])
        total_responses = len(answers)
        q_type = question.get('question_type', 'multiple_choice')

        if q_type == 'text':
            charts.append({
                'question_text': question['question_text'],
                'total_responses': total_responses,
                'is_discursive': True,
                'answers': answers
            })
        elif total_responses > 0:
            answer_counts = {}
            for answer in answers:
                answer_counts[answer] = answer_counts.get(answer, 0) + 1

            charts.append({
                'question_text': question['question_text'],
                'total_responses': total_responses,
                'is_discursive': False,
                'chart_data': {
                    'labels': list(answer_counts.keys()),
                    'datasets': [{'data': list(answer_counts.values())}]
                }
            })

    return render_template('analitico/analitico.html', charts=charts, indicadores=indicadores)