# src/routers/analitico.py

import base64
import io
import math
from itertools import cycle

from flask import Blueprint, render_template, redirect, url_for, session
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from ..config.db import get_db_connection

# cores fixas e padrão para os gráficos
FIXED_COLORS = {
    'Menos de 12 meses': '#3366CC',
    'De 1 ano a 2 anos':  '#FF9900',
    'De 3 anos a 4 anos': '#DC3912',
    'Acima de 5 anos':    '#109618'
}
DEFAULT_COLORS = [
    '#3366CC', '#FF9900', '#DC3912', '#109618',
    '#990099', '#0099C6', '#DD4477', '#66AA00',
    '#B82E2E', '#316395', '#994499', '#22AA99',
    '#AAAA11', '#6633CC', '#E67300', '#8B0707',
    '#329262', '#5574A6', '#3B3EAC', '#FF33CC'
]

analitico = Blueprint('analitico', __name__, url_prefix='/analitico')

@analitico.route('/', methods=['GET'])
def analitico_view():
    # só admin pode ver
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 1) busca todas as perguntas
    cur.execute("""
        SELECT id, question_text
          FROM form_questions
         ORDER BY order_index
    """)
    perguntas = cur.fetchall()

    charts = []
    for q in perguntas:
        qid = q['id']

        # 2) extrai diretamente as respostas que existem
        cur.execute("""
            SELECT answer AS option_label,
                   COUNT(*) AS cnt
              FROM response_answers
             WHERE question_id = %s
             GROUP BY answer
        """, (qid,))
        rows = cur.fetchall()

        # se não houver nenhuma resposta, pula
        if not rows:
            continue

        # rótulos e valores
        labels = [r['option_label'] for r in rows]
        values = [r['cnt']            for r in rows]

        # garantir sem NaN
        values = [
            0 if (v is None or (isinstance(v, float) and math.isnan(v)))
              else v
            for v in values
        ]

        # atribui cores fixas ou cíclicas
        color_cycle = cycle(DEFAULT_COLORS)
        color_map = {
            lbl: FIXED_COLORS.get(lbl, next(color_cycle))
            for lbl in labels
        }
        colors = [color_map[lbl] for lbl in labels]

        # gera gráfico de pizza
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(
            values,
            labels=None,
            colors=colors,
            autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else '',
            startangle=90,
            textprops={'fontsize': 12}
        )
        ax.axis('equal')

        # monta legenda só para valores >0
        legend = [
            {'label': lbl, 'color': color_map[lbl]}
            for lbl, cnt in zip(labels, values)
            if cnt > 0
        ]

        # converte figura em base64
        buf = io.BytesIO()
        FigureCanvas(fig).print_png(buf)
        img_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        buf.close()
        plt.close(fig)

        charts.append({
            'question_text': q['question_text'],
            'count': sum(values),
            'img_b64': img_b64,
            'legend': legend
        })

    cur.close()
    conn.close()

    return render_template('analitico/analitico.html', charts=charts)
