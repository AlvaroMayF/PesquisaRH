from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import pandas as pd
from io import BytesIO
from flask import send_file
from app.src.config.db import get_db_connection
import math
from mysql.connector import errors as mysql_errors

# NOVO IMPORT: Importa a nossa função de validação de CPF
from src.utils.validators import is_cpf_valid

admin = Blueprint('admin', __name__)


# ... (A rota admin_panel e get_rh_data continuam exatamente iguais, sem alterações)
@admin.route('/', methods=['GET'])
def admin_panel():
    if 'admin_logged_in' not in session:
        return redirect(url_for('adminLogin.admin_login'))
    username = session.get('username', 'Admin')
    return render_template('admin/admin.html', username=username)


@admin.route('/api/rh-data')
def get_rh_data():
    if 'admin_logged_in' not in session: return jsonify(error="Não autorizado"), 401
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
        kpi_where_parts = ["ativo = 1"] + base_where_clauses
        kpi_where_sql = " AND ".join(kpi_where_parts)
        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql}", base_params)
        total_ativos = cur.fetchone()['total']
        contratacoes_sql = f"SELECT COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql} AND data_admissao >= CURDATE() - INTERVAL 30 DAY"
        cur.execute(contratacoes_sql, base_params)
        novas_contratacoes_30d = cur.fetchone()['total']
        tempo_medio_sql = f"SELECT ROUND(AVG(DATEDIFF(CURDATE(), data_admissao)) / 365.25, 1) as media_anos FROM colaboradores WHERE {kpi_where_sql} AND data_admissao IS NOT NULL"
        cur.execute(tempo_medio_sql, base_params)
        media_anos_result = cur.fetchone()
        tempo_medio_anos = "N/D"
        if media_anos_result and media_anos_result['media_anos'] is not None:
            tempo_medio_anos = f"{media_anos_result['media_anos']} anos"
        faixa_etaria_sql = f"SELECT CASE WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 18 AND 25 THEN '18-25 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 26 AND 35 THEN '26-35 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 36 AND 45 THEN '36-45 anos' ELSE 'Idade não informada' END as faixa_etaria, COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql} GROUP BY faixa_etaria ORDER BY faixa_etaria"
        cur.execute(faixa_etaria_sql, base_params)
        por_faixa_etaria = cur.fetchall()
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
        tendencia_sql = "SELECT DATE_FORMAT(data_admissao, '%Y-%m') as mes, COUNT(id) as total FROM colaboradores WHERE data_admissao >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY mes ORDER BY mes ASC;"
        cur.execute(tendencia_sql)
        tendencia_contratacoes = cur.fetchall()
        table_where_clauses = base_where_clauses[:]
        table_params = base_params[:]
        table_where_clauses.append("ativo = 0" if show_inactive else "ativo = 1")
        if search_query:
            table_where_clauses.append("(nome LIKE %s OR cpf LIKE %s)")
            table_params.extend([f"%{search_query}%", f"%{search_query}%"])
        table_where_sql = " AND ".join(table_where_clauses)
        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {table_where_sql}", table_params)
        total_items = cur.fetchone()['total']
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1
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
        return jsonify(
            {'kpi': {'totalAtivos': total_ativos, 'turnover': novas_contratacoes_30d, 'tempoMedio': tempo_medio_anos},
             'chartData': {'porUnidade': {'labels': [item['unidade'] for item in por_unidade],
                                          'data': [item['total'] for item in por_unidade]},
                           'porSetor': {'labels': [item['setor'] for item in por_setor],
                                        'data': [item['total'] for item in por_setor]},
                           'porFaixaEtaria': {'labels': [item['faixa_etaria'] for item in por_faixa_etaria],
                                              'data': [item['total'] for item in por_faixa_etaria]},
                           'tendenciaContratacoes': {'labels': [item['mes'] for item in tendencia_contratacoes],
                                                     'data': [item['total'] for item in tendencia_contratacoes]}},
             'tableData': colaboradores_filtrados,
             'filters': {'unidades': unidades_disponiveis, 'setores': setores_disponiveis},
             'pagination': {'page': page, 'totalPages': total_pages, 'totalItems': total_items}})
    except Exception as e:
        print(f"Erro ao buscar dados para o dashboard: {e}")
        return jsonify(error=str(e)), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/colaborador/add', methods=['POST'])
def add_new_colaborator():
    if 'admin_logged_in' not in session: return jsonify(success=False, message="Acesso não autorizado."), 401
    conn = None
    try:
        # Pega os dados brutos do formulário
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        cargo = request.form.get('cargo')
        setor = request.form.get('setor')
        unidade = request.form.get('unidade')
        data_admissao = request.form.get('data_admissao')

        # VALIDAÇÃO DE CAMPOS OBRIGATÓRIOS
        if not all([nome, cpf, data_nascimento, cargo, setor, unidade, data_admissao]):
            return jsonify(success=False, message="Todos os campos são obrigatórios."), 400

        # ========== INÍCIO DA VALIDAÇÃO E PADRONIZAÇÃO ==========
        # 1. Validação de CPF
        if not is_cpf_valid(cpf):
            return jsonify(success=False, message="O CPF informado é inválido."), 400

        # 2. Padronização dos dados de texto
        nome_padronizado = nome.strip().upper()
        cargo_padronizado = cargo.strip().upper()
        setor_padronizado = setor.strip().upper()
        # A unidade já vem de um dropdown, então não precisa padronizar.
        # ========== FIM DA VALIDAÇÃO E PADRONIZAÇÃO ==========

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM colaboradores WHERE cpf = %s", (cpf,))
        if cur.fetchone():
            return jsonify(success=False, message=f"CPF '{cpf}' já está cadastrado."), 409

        sql = "INSERT INTO colaboradores (nome, data_nascimento, cpf, setor, cargo, unidade, data_admissao, ativo) VALUES (%s, %s, %s, %s, %s, %s, %s, 1)"
        # Usa as variáveis padronizadas para inserir no banco
        params = (nome_padronizado, data_nascimento, cpf, setor_padronizado, cargo_padronizado, unidade, data_admissao)

        cur.execute(sql, params)
        conn.commit()
        cur.close()
        return jsonify(success=True, message="Colaborador cadastrado com sucesso!")
    except mysql_errors.IntegrityError as e:
        print(f"Erro de integridade ao cadastrar: {e}")
        return jsonify(success=False, message="Erro de dados. Verifique se o CPF já foi cadastrado."), 409
    except Exception as e:
        print(f"Erro inesperado ao cadastrar novo colaborador: {e}")
        return jsonify(success=False, message="Ocorreu um erro ao salvar os dados."), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/colaborador/edit/<int:colaborador_id>', methods=['POST'])
def edit_colaborador_data(colaborador_id):
    if 'admin_logged_in' not in session:
        return jsonify(success=False, message="Acesso não autorizado."), 401
    conn = None
    try:
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        cargo = request.form.get('cargo')
        setor = request.form.get('setor')
        unidade = request.form.get('unidade')
        data_admissao = request.form.get('data_admissao')

        # ========== INÍCIO DA VALIDAÇÃO E PADRONIZAÇÃO ==========
        # 1. Validação de CPF
        if not is_cpf_valid(cpf):
            return jsonify(success=False, message="O CPF informado é inválido."), 400

        # 2. Padronização dos dados de texto
        nome_padronizado = nome.strip().upper()
        cargo_padronizado = cargo.strip().upper()
        setor_padronizado = setor.strip().upper()
        # ========== FIM DA VALIDAÇÃO E PADRONIZAÇÃO ==========

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM colaboradores WHERE cpf = %s AND id != %s", (cpf, colaborador_id))
        if cur.fetchone():
            return jsonify(success=False, message=f"CPF '{cpf}' já pertence a outro colaborador."), 409

        sql = "UPDATE colaboradores SET nome = %s, cpf = %s, data_nascimento = %s, setor = %s, cargo = %s, unidade = %s, data_admissao = %s WHERE id = %s"
        # Usa as variáveis padronizadas para atualizar o banco
        params = (nome_padronizado, cpf, data_nascimento, setor_padronizado, cargo_padronizado, unidade, data_admissao,
                  colaborador_id)

        cur.execute(sql, params)
        conn.commit()
        cur.close()
        return jsonify(success=True, message="Colaborador atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao editar colaborador {colaborador_id}: {e}")
        return jsonify(success=False, message="Erro ao salvar as alterações."), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


# ... (O restante do arquivo com as rotas de toggle, get_colaborador, export e autocomplete continua aqui, sem alterações)
@admin.route('/colaborador/toggle-status/<int:colaborador_id>', methods=['POST'])
def toggle_colaborator_status(colaborador_id):
    if 'admin_logged_in' not in session: return jsonify(success=False, message="Acesso não autorizado."), 401
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT nome, ativo FROM colaboradores WHERE id = %s", (colaborador_id,))
        colaborador = cur.fetchone()
        if not colaborador:
            return jsonify(success=False, message="Colaborador não encontrado."), 404
        current_status = colaborador['ativo']
        new_status = 0 if current_status == 1 else 1
        status_texto = "inativado" if new_status == 0 else "reativado"
        cur.execute("UPDATE colaboradores SET ativo = %s WHERE id = %s", (new_status, colaborador_id))
        conn.commit()
        cur.close()
        return jsonify(success=True, message="Status alterado com sucesso.",
                       data={'nome': colaborador['nome'], 'status_texto': status_texto})
    except Exception as e:
        print(f"Erro ao alterar status do colaborador {colaborador_id}: {e}")
        return jsonify(success=False, message="Erro ao alterar o status."), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/colaborador/<int:colaborador_id>', methods=['GET'])
def get_colaborador_data(colaborador_id):
    if 'admin_logged_in' not in session:
        return jsonify(success=False, message="Acesso não autorizado."), 401
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, nome, cpf, data_nascimento, setor, cargo, unidade, data_admissao FROM colaboradores WHERE id = %s",
            (colaborador_id,))
        colaborador = cur.fetchone()
        cur.close()
        if colaborador:
            if colaborador.get('data_nascimento'):
                colaborador['data_nascimento'] = colaborador['data_nascimento'].strftime('%Y-%m-%d')
            if colaborador.get('data_admissao'):
                colaborador['data_admissao'] = colaborador['data_admissao'].strftime('%Y-%m-%d')
            return jsonify(success=True, data=colaborador)
        else:
            return jsonify(success=False, message="Colaborador não encontrado."), 404
    except Exception as e:
        print(f"Erro ao buscar dados do colaborador {colaborador_id}: {e}")
        return jsonify(success=False, message="Erro ao buscar dados."), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/export-data')
def export_data():
    if 'admin_logged_in' not in session:
        return "Não autorizado", 401
    conn = None
    try:
        unidade_filtro = request.args.get('unidade')
        setor_filtro = request.args.get('setor')
        search_query = request.args.get('search')
        show_inactive = request.args.get('inactive', 'false').lower() == 'true'
        base_where_clauses = []
        base_params = []
        if unidade_filtro:
            base_where_clauses.append("unidade = %s")
            base_params.append(unidade_filtro)
        if setor_filtro:
            base_where_clauses.append("setor = %s")
            base_params.append(setor_filtro)
        table_where_clauses = base_where_clauses[:]
        table_params = base_params[:]
        table_where_clauses.append("ativo = 0" if show_inactive else "ativo = 1")
        if search_query:
            table_where_clauses.append("(nome LIKE %s OR cpf LIKE %s)")
            table_params.extend([f"%{search_query}%", f"%{search_query}%"])
        table_where_sql = " AND ".join(table_where_clauses)
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        query = f"SELECT nome, data_nascimento, cpf, setor, cargo, unidade, data_admissao FROM colaboradores WHERE {table_where_sql} ORDER BY nome ASC"
        cur.execute(query, table_params)
        colaboradores = cur.fetchall()
        cur.close()
        df = pd.DataFrame(colaboradores)
        df.rename(columns={
            'nome': 'Nome Completo',
            'data_nascimento': 'Data de Nascimento',
            'cpf': 'CPF',
            'setor': 'Setor',
            'cargo': 'Cargo',
            'unidade': 'Unidade',
            'data_admissao': 'Data de Admissão'
        }, inplace=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Colaboradores')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='relatorio_colaboradores.xlsx'
        )
    except Exception as e:
        print(f"Erro ao exportar dados: {e}")
        return "Erro ao gerar o relatório.", 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/get-setores')
def get_all_setores():
    if 'admin_logged_in' not in session:
        return jsonify(error="Não autorizado"), 401
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT DISTINCT setor FROM colaboradores WHERE setor IS NOT NULL AND setor != '' ORDER BY setor ASC")
        setores = [row['setor'] for row in cur.fetchall()]
        cur.close()
        return jsonify(setores)
    except Exception as e:
        print(f"Erro ao buscar lista de setores: {e}")
        return jsonify([]), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@admin.route('/api/get-cargos')
def get_all_cargos():
    if 'admin_logged_in' not in session:
        return jsonify(error="Não autorizado"), 401
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT DISTINCT cargo FROM colaboradores WHERE cargo IS NOT NULL AND cargo != '' ORDER BY cargo ASC")
        cargos = [row['cargo'] for row in cur.fetchall()]
        cur.close()
        return jsonify(cargos)
    except Exception as e:
        print(f"Erro ao buscar lista de cargos: {e}")
        return jsonify([]), 500
    finally:
        if conn and conn.is_connected():
            conn.close()