from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from app.src.config.db import get_db_connection
import math

admin = Blueprint('admin', __name__)


@admin.route('/admin/', methods=['GET'])
def admin_panel():
    if 'admin_logged_in' not in session:
        return redirect(url_for('adminLogin.admin_login'))
    username = session.get('username', 'Admin')
    return render_template('admin/admin.html', username=username)


@admin.route('/api/rh-data')
def get_rh_data():
    if 'admin_logged_in' not in session:
        return jsonify(error="Não autorizado"), 401

    conn = None
    try:
        unidade_filtro = request.args.get('unidade')
        setor_filtro = request.args.get('setor')
        search_query = request.args.get('search')
        show_inactive = request.args.get('inactive', 'false').lower() == 'true'
        try:
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            page = 1
        ITEMS_PER_PAGE = 15

        base_where_clauses = []
        base_params = []
        if unidade_filtro:
            base_where_clauses.append("unidade = %s")
            base_params.append(unidade_filtro)
        if setor_filtro:
            base_where_clauses.append("setor = %s")
            base_params.append(setor_filtro)

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        kpi_where_sql = " AND ".join(["ativo = 1"] + base_where_clauses)
        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql}", base_params)
        total_ativos = cur.fetchone()['total']

        cur.execute(
            "SELECT unidade, COUNT(*) as total FROM colaboradores WHERE ativo = 1 AND unidade IS NOT NULL GROUP BY unidade ORDER BY total DESC")
        por_unidade = cur.fetchall()

        setor_chart_sql = "SELECT setor, COUNT(*) as total FROM colaboradores WHERE ativo = 1 AND setor IS NOT NULL"
        setor_chart_params = []
        if unidade_filtro:
            setor_chart_sql += " AND unidade = %s"
            setor_chart_params.append(unidade_filtro)
        setor_chart_sql += " GROUP BY setor ORDER BY total DESC LIMIT 10"
        cur.execute(setor_chart_sql, setor_chart_params)
        por_setor = cur.fetchall()

        cur.execute(
            "SELECT CASE WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 18 AND 25 THEN '18-25 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 26 AND 35 THEN '26-35 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 36 AND 45 THEN '36-45 anos' ELSE 'Mais de 45 anos' END as faixa_etaria, COUNT(*) as total FROM colaboradores WHERE ativo = 1 GROUP BY faixa_etaria ORDER BY faixa_etaria")
        por_faixa_etaria = cur.fetchall()

        table_where_clauses = base_where_clauses[:]
        table_params = base_params[:]
        table_where_clauses.append("ativo = 0" if show_inactive else "ativo = 1")
        if search_query:
            table_where_clauses.append("(nome LIKE %s OR cpf LIKE %s)")
            table_params.extend([f"%{search_query}%", f"%{search_query}%"])
        table_where_sql = " AND ".join(table_where_clauses)

        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {table_where_sql}", table_params)
        total_items = cur.fetchone()['total']
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
        offset = (page - 1) * ITEMS_PER_PAGE

        cur.execute(
            f"SELECT id, nome, cpf, setor, cargo, unidade, ativo FROM colaboradores WHERE {table_where_sql} ORDER BY nome ASC LIMIT %s OFFSET %s",
            table_params + [ITEMS_PER_PAGE, offset])
        colaboradores_filtrados = cur.fetchall()

        cur.execute("SELECT DISTINCT unidade FROM colaboradores WHERE unidade IS NOT NULL ORDER BY unidade")
        unidades_disponiveis = [row['unidade'] for row in cur.fetchall()]

        setores_disponiveis = []
        if unidade_filtro:
            cur.execute(
                "SELECT DISTINCT setor FROM colaboradores WHERE setor IS NOT NULL AND unidade = %s ORDER BY setor",
                (unidade_filtro,))
            setores_disponiveis = [row['setor'] for row in cur.fetchall()]

        cur.close()

        return jsonify({
            'kpi': {'totalAtivos': total_ativos, 'turnover': 'N/D', 'tempoMedio': 'N/D'},
            'chartData': {
                'porUnidade': {'labels': [item['unidade'] for item in por_unidade],
                               'data': [item['total'] for item in por_unidade]},
                'porSetor': {'labels': [item['setor'] for item in por_setor],
                             'data': [item['total'] for item in por_setor]},
                'porFaixaEtaria': {'labels': [item['faixa_etaria'] for item in por_faixa_etaria],
                                   'data': [item['total'] for item in por_faixa_etaria]}
            },
            'tableData': colaboradores_filtrados,
            'filters': {'unidades': unidades_disponiveis, 'setores': setores_disponiveis},
            'pagination': {'page': page, 'totalPages': total_pages, 'totalItems': total_items}
        })

    except Exception as e:
        print(f"Erro ao buscar dados para o dashboard: {e}")
        return jsonify(error=str(e)), 500
    finally:
        if conn and conn.is_connected():
            conn.close()