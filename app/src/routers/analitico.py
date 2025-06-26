# src/routers/analitico.py

import json
from itertools import cycle
from flask import Blueprint, render_template, redirect, url_for, session

from ..config.db import get_db_connection

# Cores para os gráficos
FIXED_COLORS = {
    'Menos de 12 meses': '#3366CC',
    'De 1 ano a 2 anos': '#FF9900',
    'De 3 anos a 4 anos': '#DC3912',
    'Acima de 5 anos': '#109618'
}
DEFAULT_COLORS = [
    '#3366CC', '#FF9900', '#DC3912', '#109618', '#990099', '#0099C6',
    '#DD4477', '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99'
]

analitico = Blueprint('analitico', __name__, url_prefix='/analitico')


@analitico.route('/', methods=['GET'])
def analitico_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Otimização: Busca todas as respostas de uma só vez
    query = """
        SELECT 
            q.id AS question_id,
            q.question_text,
            ra.answer,
            COUNT(ra.id) AS count
        FROM form_questions q
        JOIN response_answers ra ON q.id = ra.question_id
        GROUP BY q.id, q.question_text, ra.answer
        ORDER BY q.order_index, count DESC;
    """
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()

    # Processa os resultados em Python
    charts_data = {}
    for row in results:
        qid = row['question_id']
        if qid not in charts_data:
            charts_data[qid] = {
                'question_text': row['question_text'],
                'labels': [],
                'values': [],
                'total_responses': 0
            }
        charts_data[qid]['labels'].append(row['answer'])
        charts_data[qid]['values'].append(row['count'])
        charts_data[qid]['total_responses'] += row['count']

    # Prepara os dados finais para o template
    charts = []
    for qid, data in charts_data.items():
        color_cycle = cycle(DEFAULT_COLORS)
        colors = [FIXED_COLORS.get(label, next(color_cycle)) for label in data['labels']]

        charts.append({
            'question_text': data['question_text'],
            'total_responses': data['total_responses'],
            # Converte os dados para JSON para serem usados pelo JavaScript
            'chart_data': json.dumps({
                'labels': data['labels'],
                'datasets': [{
                    'data': data['values'],
                    'backgroundColor': colors
                }]
            })
        })

    return render_template('analitico/analitico.html', charts=charts)
