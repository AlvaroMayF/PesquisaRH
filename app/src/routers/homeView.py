# app/src/routers/homeView.py

from flask import Blueprint, render_template, request
from src.config.db import get_db_connection
from datetime import date, timedelta
import calendar

home = Blueprint('home', __name__, url_prefix='')

@home.route('/', methods=['GET'])
def home_view():
    """
    Renderiza o painel RH com métricas dinâmicas e sparklines.
    """
    # Conecta ao banco
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # 1) Totais
    cur.execute('SELECT COUNT(*) AS total_colab FROM colaboradores')
    total_colaboradores = cur.fetchone()['total_colab']

    cur.execute('SELECT COUNT(*) AS total_resp FROM responses')
    total_respondidas = cur.fetchone()['total_resp']

    cur.execute('SELECT COUNT(*) AS total_pending '
                'FROM colaboradores '
                'WHERE respondeu = 0')
    total_pesquisas_pendentes = cur.fetchone()['total_pending']

    cur.execute(
        'SELECT COUNT(*) AS total_aniv '
        'FROM colaboradores '
        'WHERE MONTH(data_nascimento) = MONTH(CURDATE())'
    )
    total_aniversariantes = cur.fetchone()['total_aniv']

    # 2) Sparklines (últimos 6 meses de respostas)
    seis_meses_atras = date.today().replace(day=1) - timedelta(days=180)
    cur.execute(
        '''
        SELECT MONTH(submitted_at) AS mes, COUNT(*) AS qtd
        FROM responses
        WHERE submitted_at >= %s
        GROUP BY mes
        ORDER BY mes
        ''',
        (seis_meses_atras,)
    )
    rows = cur.fetchall()
    conn.close()

    # Prepara labels e dados para sparklines
    labels = []
    data = []
    for i in range(6, 0, -1):
        dt = date.today().replace(day=1) - timedelta(days=30 * i)
        m = dt.month
        labels.append(calendar.month_abbr[m])
        data.append(next((r['qtd'] for r in rows if r['mes'] == m), 0))

    # Renderiza template com todas as variáveis
    return render_template(
        'home/home.html',
        active_endpoint=request.endpoint,
        total_colaboradores=total_colaboradores,
        total_respondidas=total_respondidas,
        total_pesquisas_pendentes=total_pesquisas_pendentes,
        total_aniversariantes=total_aniversariantes,
        sparkline_labels=labels,
        sparkline_data=data
    )
