# src/routers/analitico.py

from flask import Blueprint, render_template, redirect, url_for, session
from ..config.db import get_db_connection

analitico = Blueprint('analitico', __name__, url_prefix='/analitico')

# --- INÍCIO DA ADIÇÃO: ORDEM PADRÃO DAS LEGENDAS ---
# Esta lista define a ordem em que as legendas devem aparecer nos gráficos.
STANDARD_LEGEND_ORDER = [
    'Muito Satisfeito',
    'Satisfeito',
    'Neutro',
    'Insatisfeito',
    'Muito Insatisfeito',
    'Ótimo',
    'Bom',
    'Regular',
    'Ruim',
    'Sim',
    'Não',
    'Menos de 12 meses',
    'De 1 ano a 2 anos',
    'De 3 anos a 4 anos',
    'De 3 anos a 4 ano:',  # Variação com ":" para garantir a captura
    'Acima de 5 anos'
]


# --- FIM DA ADIÇÃO ---


@analitico.route('/')
def analitico_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(id) AS total_colaboradores FROM colaboradores")
    total_colaboradores = cur.fetchone()['total_colaboradores']

    cur.execute("SELECT COUNT(id) AS pesquisas_respondidas FROM colaboradores WHERE respondeu = 1")
    pesquisas_respondidas = cur.fetchone()['pesquisas_respondidas']

    taxa_participacao = 0
    if total_colaboradores > 0:
        taxa_participacao = round((pesquisas_respondidas / total_colaboradores) * 100)

    indicadores = {
        'total_colaboradores': total_colaboradores,
        'pesquisas_respondidas': pesquisas_respondidas,
        'taxa_participacao': taxa_participacao
    }

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

            # --- INÍCIO DA NOVA LÓGICA DE ORDENAÇÃO ---
            sorted_labels = []
            sorted_data = []

            # Adiciona primeiro os itens na ordem padrão definida
            for item in STANDARD_LEGEND_ORDER:
                if item in answer_counts:
                    sorted_labels.append(item)
                    sorted_data.append(answer_counts.pop(item))  # .pop() remove o item para não ser adicionado de novo

            # Adiciona quaisquer outros itens que não estavam na lista padrão
            for item, count in answer_counts.items():
                sorted_labels.append(item)
                sorted_data.append(count)
            # --- FIM DA NOVA LÓGICA DE ORDENAÇÃO ---

            charts.append({
                'question_text': question['question_text'],
                'total_responses': total_responses,
                'is_discursive': False,
                'chart_data': {
                    'labels': sorted_labels,  # Usa a lista de legendas ordenada
                    'datasets': [{'data': sorted_data}]  # Usa a lista de dados ordenada
                }
            })

    return render_template('analitico/analitico.html', charts=charts, indicadores=indicadores)