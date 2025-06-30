# app/src/routers/homeView.py

from flask import Blueprint, render_template, request, session
from ..config.db import get_db_connection
from datetime import date, timedelta
import calendar
import locale

# Configura o locale para português do Brasil para formatar as datas
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não pôde ser configurado.")


home = Blueprint('home', __name__, url_prefix='')


@home.route('/', methods=['GET'])
def home_view():
    """
    Renderiza o painel RH com métricas dinâmicas, sparklines, o último comunicado e o próximo feriado.
    """
    # Inicializa as variáveis para evitar erros caso a consulta falhe
    total_colaboradores = 0
    total_respondidas = 0
    total_pesquisas_pendentes = 0
    aniversariantes = []
    ultimo_comunicado = None
    proximo_feriado = None
    labels = []
    data = []

    try:
        # Conecta ao banco
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # 1) Totais (código existente)
        cur.execute('SELECT COUNT(*) AS total_colab FROM colaboradores WHERE ativo = 1')
        total_colaboradores = cur.fetchone()['total_colab']

        cur.execute('SELECT COUNT(*) AS total_resp FROM colaboradores WHERE respondeu = 1 AND ativo = 1')
        total_respondidas = cur.fetchone()['total_resp']

        cur.execute('SELECT COUNT(*) AS total_pending FROM colaboradores WHERE respondeu = 0 AND ativo = 1')
        total_pesquisas_pendentes = cur.fetchone()['total_pending']

        # --- CORREÇÃO APLICADA AQUI ---
        # Aniversariantes do dia (agora busca somente o nome)
        cur.execute(
            'SELECT nome FROM colaboradores WHERE MONTH(data_nascimento) = MONTH(CURDATE()) AND DAY(data_nascimento) = DAY(CURDATE()) AND ativo = 1'
        )
        aniversariantes = cur.fetchall()

        # 2) Sparklines (código existente)
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

        # 3) Busca o último comunicado (código existente)
        cur.execute("""
            SELECT titulo, conteudo 
            FROM comunicados 
            ORDER BY data_publicacao DESC 
            LIMIT 1
        """)
        ultimo_comunicado = cur.fetchone()

        # Busca o próximo feriado do banco de dados
        cur.execute("""
            SELECT 
                f.data,
                f.descricao,
                u.nome AS unidade
            FROM feriados f
            JOIN unidades u ON f.unidade_id = u.id
            WHERE f.data >= CURDATE()
            ORDER BY f.data ASC
            LIMIT 1
        """)
        proximo_feriado = cur.fetchone()

        cur.close()
        conn.close()

        # Prepara labels e dados para sparklines
        for i in range(5, -1, -1):
            dt = date.today() - timedelta(days=30 * i)
            m = dt.month
            # Garante que o nome do mês seja capitalizado
            labels.append(calendar.month_abbr[m].capitalize())
            data.append(next((r['qtd'] for r in rows if r['mes'] == m), 0))

    except Exception as e:
        print(f"Erro ao buscar dados para a home page: {e}")

    # Renderiza template com todas as variáveis
    return render_template(
        'home/home.html',
        active_endpoint=request.endpoint,
        total_colaboradores=total_colaboradores,
        total_respondidas=total_respondidas,
        total_pesquisas_pendentes=total_pesquisas_pendentes,
        aniversariantes=aniversariantes,
        sparkline_labels=labels,
        sparkline_data=data,
        ultimo_comunicado=ultimo_comunicado,
        proximo_feriado=proximo_feriado
    )
