# src/routers/analitico.py
import base64
import io
import math
from itertools import cycle
from flask import Blueprint, render_template, redirect, url_for, session
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from ..config.db import get_db_connection

# Cores fixas e padrão para os gráficos
FIXED_COLORS = {
    'Menos de 12 meses': '#3366CC',
    'De 1 ano a 2 anos': '#FF9900',
    'De 3 anos a 4 anos': '#DC3912',
    'Acima de 5 anos': '#109618'
}

DEFAULT_COLORS = [
    '#3366CC', '#FF9900', '#DC3912', '#109618', '#990099', '#0099C6', '#DD4477',
    '#66AA00', '#B82E2E', '#316395', '#994499', '#22AA99', '#AAAA11', '#6633CC',
    '#E67300', '#8B0707', '#329262', '#5574A6', '#3B3EAC', '#FF33CC'
]

# Sincroniza opções novas no banco

def sincronizar_opcoes_conectado(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT question_id, answer FROM response_answers")
    respostas = cur.fetchall()
    novas = 0
    for question_id, resposta in respostas:
        cur.execute(
            "SELECT 1 FROM form_options WHERE question_id = ? AND option_label = ?",
            (question_id, resposta)
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO form_options (question_id, option_label, option_value) VALUES (?, ?, ?)",
                (question_id, resposta, resposta)
            )
            novas += 1
    if novas > 0:
        conn.commit()

# Blueprint para rotas analíticas
analitico = Blueprint('analitico', __name__, url_prefix='/analitico')

@analitico.route('/', methods=['GET'])
def analitico_view():
    """
    Gera gráficos de pizza para cada pergunta e exibe na página analítica.
    """
    # Verifica autenticação de admin
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    sincronizar_opcoes_conectado(conn)

    charts = []
    perguntas = conn.execute(
        'SELECT id, question_text FROM form_questions ORDER BY order_index'
    ).fetchall()

    for q in perguntas:
        opcoes = conn.execute(
            'SELECT DISTINCT option_label '
            'FROM form_options '
            'WHERE question_id = ? '
            'ORDER BY option_label',
            (q['id'],)
        ).fetchall()
        all_labels = [o['option_label'] for o in opcoes]

        rows = conn.execute(
            '''
            SELECT answer AS option_label, COUNT(*) AS cnt
            FROM response_answers
            WHERE question_id = ?
            GROUP BY answer
            ''',
            (q['id'],)
        ).fetchall()
        contagem = {r['option_label']: r['cnt'] for r in rows}

        labels = all_labels
        values = [contagem.get(label, 0) for label in labels]
        values = [0 if (v is None or isinstance(v, float) and math.isnan(v)) else v for v in values]

        if sum(values) == 0:
            continue

        color_cycle = cycle(DEFAULT_COLORS)
        color_map = {label: FIXED_COLORS.get(label, next(color_cycle)) for label in labels}
        colors = [color_map[label] for label in labels]

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

        legend_items = [
            {'label': label, 'color': color_map[label]}
            for label, v in zip(labels, values)
            if v > 0 and not label.lower().startswith('opção')
        ]

        buf = io.BytesIO()
        FigureCanvas(fig).print_png(buf)
        img_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        buf.close()
        plt.close(fig)

        charts.append({
            'question_text': q['question_text'],
            'count': sum(values),
            'img_b64': img_b64,
            'legend': legend_items
        })

    conn.close()
    return render_template('analitico/analitico.html', charts=charts)
