# src/routers/analitico.py

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from ..config.db import get_db_connection

analitico = Blueprint('analitico', __name__, url_prefix='/analitico')

MINIMUM_RESPONDENTS = 3

STANDARD_LEGEND_ORDER = [
    'Muito Satisfeito', 'Satisfeito', 'Neutro', 'Insatisfeito', 'Muito Insatisfeito',
    'Ótimo', 'Bom', 'Regular', 'Ruim', 'Sim', 'Não', 'Menos de 12 meses',
    'De 1 ano a 2 anos', 'De 3 anos a 4 anos', 'De 3 anos a 4 ano:', 'Acima de 5 anos'
]


@analitico.route('/')
def analitico_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    selected_unidade = request.args.get('unidade', '')
    selected_setor = request.args.get('setor', '')
    selected_cargo = request.args.get('cargo', '')

    params = []

    where_conditions_responses = []
    if selected_unidade:
        where_conditions_responses.append("r.colaborador_unidade = %s")
        params.append(selected_unidade)
    if selected_setor:
        where_conditions_responses.append("r.colaborador_setor = %s")
        params.append(selected_setor)
    if selected_cargo:
        where_conditions_responses.append("r.colaborador_cargo = %s")
        params.append(selected_cargo)

    where_clause_responses = " AND ".join(where_conditions_responses) if where_conditions_responses else "1=1"

    where_conditions_colabs = []
    if selected_unidade:
        where_conditions_colabs.append("unidade = %s")
    if selected_setor:
        where_conditions_colabs.append("setor = %s")
    if selected_cargo:
        where_conditions_colabs.append("cargo = %s")

    where_clause_colabs = " AND ".join(where_conditions_colabs) if where_conditions_colabs else "1=1"

    cur.execute(
        "SELECT DISTINCT unidade FROM colaboradores WHERE unidade IS NOT NULL AND unidade != '' ORDER BY unidade")
    unidades = [row['unidade'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT setor FROM colaboradores WHERE setor IS NOT NULL AND setor != '' ORDER BY setor")
    setores = [row['setor'] for row in cur.fetchall()]
    cur.execute("SELECT DISTINCT cargo FROM colaboradores WHERE cargo IS NOT NULL AND cargo != '' ORDER BY cargo")
    cargos = [row['cargo'] for row in cur.fetchall()]

    count_query = f"SELECT COUNT(*) as count FROM responses r WHERE {where_clause_responses}"
    cur.execute(count_query, tuple(params))
    total_responses_for_filter = cur.fetchone()['count']

    charts = []
    if total_responses_for_filter >= MINIMUM_RESPONDENTS:
        query = f"""
            SELECT q.id, q.question_text, q.question_type, ra.answer
            FROM responses r
            JOIN response_answers ra ON r.id = ra.response_id
            JOIN form_questions q ON ra.question_id = q.id
            WHERE {where_clause_responses}
            ORDER BY q.order_index
        """
        cur.execute(query, tuple(params))
        all_answers_filtered = cur.fetchall()

        answers_by_qid = {}
        questions_map = {}
        for row in all_answers_filtered:
            qid = row['id']
            if qid not in answers_by_qid:
                answers_by_qid[qid] = []
                questions_map[qid] = {'question_text': row['question_text'], 'question_type': row['question_type']}
            if row['answer'] and row['answer'].strip():
                answers_by_qid[qid].append(row['answer'])

        for qid, question_data in questions_map.items():
            answers = answers_by_qid.get(qid, [])
            total_responses = len(answers)
            if question_data['question_type'] == 'text':
                charts.append({'question_text': question_data['question_text'], 'total_responses': total_responses,
                               'is_discursive': True, 'answers': answers})
            elif total_responses > 0:
                answer_counts = {a: answers.count(a) for a in set(answers)}
                sorted_labels, sorted_data = [], []
                for item in STANDARD_LEGEND_ORDER:
                    if item in answer_counts:
                        sorted_labels.append(item)
                        sorted_data.append(answer_counts.pop(item))
                for item, count in answer_counts.items():
                    sorted_labels.append(item)
                    sorted_data.append(count)
                charts.append({'question_text': question_data['question_text'], 'total_responses': total_responses,
                               'is_discursive': False,
                               'chart_data': {'labels': sorted_labels, 'datasets': [{'data': sorted_data}]}})

    # A linha abaixo foi removida para evitar que a mensagem "vaze" para outras páginas
    # elif any(request.args.values()):
    #     flash(f'Não há dados suficientes...', 'warning')

    cur.execute(f"SELECT COUNT(id) AS total FROM colaboradores WHERE {where_clause_colabs}", tuple(params))
    total_colaboradores = cur.fetchone()['total']

    cur.execute(f"SELECT COUNT(id) as count FROM responses r WHERE {where_clause_responses}", tuple(params))
    pesquisas_respondidas = cur.fetchone()['count']

    taxa_participacao = round((pesquisas_respondidas / total_colaboradores) * 100, 1) if total_colaboradores > 0 else 0

    indicadores = {'total_colaboradores': total_colaboradores, 'pesquisas_respondidas': pesquisas_respondidas,
                   'taxa_participacao': taxa_participacao}

    cur.close()
    conn.close()

    return render_template('analitico/analitico.html',
                           charts=charts,
                           indicadores=indicadores,
                           unidades=unidades,
                           setores=setores,
                           cargos=cargos)