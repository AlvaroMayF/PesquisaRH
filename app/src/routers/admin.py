# Arquivo: src/routers/admin.py

from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request, current_app, \
    send_from_directory
from PIL import Image
from io import BytesIO
import pandas as pd
from app.src.config.db import get_db_connection
import math
from mysql.connector import errors as mysql_errors
import os
import time
import base64
from werkzeug.utils import secure_filename
from src.utils.validators import is_cpf_valid
# ATUALIZAÇÃO: Importa as funções corretas para o fluxo final
from src.services.idsecure_db_service import create_idsecure_user, add_photo_to_idsecure, trigger_idsecure_sync

admin = Blueprint('admin', __name__, url_prefix='/admin')


# --- FUNÇÕES AUXILIARES ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_photo(request_obj):
    base_path = current_app.config.get('FOTOS_FOLDER')
    if not base_path: return None, "ERRO DE CONFIGURAÇÃO: 'FOTOS_FOLDER' não foi definida."
    try:
        os.makedirs(base_path, exist_ok=True)
    except Exception as e:
        return None, f"ERRO DE PERMISSÃO: Não foi possível criar o diretório '{base_path}': {e}"
    timestamp = int(time.time())
    foto_upload = request.files.get('foto')
    if foto_upload and foto_upload.filename != '' and allowed_file(foto_upload.filename):
        try:
            img = Image.open(foto_upload.stream)
            rgb_img = img.convert('RGB')
            base_filename = os.path.splitext(secure_filename(foto_upload.filename))[0]
            foto_filename = f"{timestamp}_{base_filename}.jpg"
            save_path = os.path.join(base_path, foto_filename)
            rgb_img.save(save_path, 'jpeg', quality=90)
            return foto_filename, None
        except Exception as e:
            return None, f"ERRO AO PROCESSAR IMAGEM ANEXADA: {e}"
    elif 'foto_base64' in request.form and request.form['foto_base64']:
        try:
            if ',' in request.form['foto_base64']:
                img_data_str = request.form['foto_base64'].split(',')[1]
                img_data = base64.b64decode(img_data_str)
                img = Image.open(BytesIO(img_data))
                rgb_img = img.convert('RGB')
                foto_filename = f"webcam_{timestamp}.jpg"
                save_path = os.path.join(base_path, foto_filename)
                rgb_img.save(save_path, 'jpeg', quality=90)
                return foto_filename, None
        except Exception as e:
            return None, f"ERRO AO PROCESSAR IMAGEM DA WEBCAM: {e}"
    return None, None


def close_safe(conn, cur):
    if cur:
        try:
            cur.close()
        except:
            pass
    if conn and conn.is_connected():
        try:
            conn.close()
        except:
            pass


# --- ROTAS ---
@admin.route('/', methods=['GET'])
def admin_panel():
    if 'admin_logged_in' not in session: return redirect(url_for('adminLogin.admin_login'))
    return render_template('admin/admin.html')


@admin.route('/api/rh-data')
def get_rh_data():
    if 'admin_logged_in' not in session: return jsonify(error="Não autorizado"), 401
    conn, cur = None, None
    try:
        conn = get_db_connection()
        if not conn or not conn.is_connected():
            return jsonify(error="Falha na conexão com o banco de dados do RH."), 500
        cur = conn.cursor(dictionary=True)
        unidade_filtro = request.args.get('unidade')
        setor_filtro = request.args.get('setor')
        search_query = request.args.get('search')
        show_inactive = request.args.get('inactive', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        ITEMS_PER_PAGE = 15
        base_where_clauses, base_params = [], []
        if unidade_filtro: base_where_clauses.append("unidade = %s"); base_params.append(unidade_filtro)
        if setor_filtro: base_where_clauses.append("setor = %s"); base_params.append(setor_filtro)
        kpi_where_parts = ["ativo = 1"] + base_where_clauses
        kpi_where_sql = " AND ".join(kpi_where_parts)
        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql}", base_params)
        total_ativos = (cur.fetchone() or {}).get('total', 0)
        cur.execute(
            f"SELECT COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql} AND data_admissao >= CURDATE() - INTERVAL 30 DAY",
            base_params)
        novas_contratacoes_30d = (cur.fetchone() or {}).get('total', 0)
        cur.execute(
            f"SELECT ROUND(AVG(DATEDIFF(CURDATE(), data_admissao)) / 365.25, 1) as media_anos FROM colaboradores WHERE {kpi_where_sql} AND data_admissao IS NOT NULL",
            base_params)
        media_anos_result = cur.fetchone()
        tempo_medio_anos = f"{media_anos_result['media_anos']} anos" if media_anos_result and media_anos_result.get(
            'media_anos') is not None else "N/D"
        faixa_etaria_sql = f"SELECT CASE WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 18 AND 25 THEN '18-25 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 26 AND 35 THEN '26-35 anos' WHEN (YEAR(CURDATE()) - YEAR(data_nascimento)) BETWEEN 36 AND 45 THEN '36-45 anos' ELSE 'Idade não informada' END as faixa_etaria, COUNT(*) as total FROM colaboradores WHERE {kpi_where_sql} GROUP BY faixa_etaria ORDER BY faixa_etaria"
        cur.execute(faixa_etaria_sql, base_params)
        por_faixa_etaria = cur.fetchall()
        cur.execute(
            "SELECT unidade, COUNT(*) as total FROM colaboradores WHERE ativo = 1 AND unidade IS NOT NULL GROUP BY unidade ORDER BY total DESC")
        por_unidade = cur.fetchall()
        setor_chart_sql = "SELECT setor, COUNT(*) as total FROM colaboradores WHERE ativo = 1 AND setor IS NOT NULL"
        setor_chart_params = []
        if unidade_filtro: setor_chart_sql += " AND unidade = %s"; setor_chart_params.append(unidade_filtro)
        setor_chart_sql += " GROUP BY setor ORDER BY total DESC LIMIT 10"
        cur.execute(setor_chart_sql, setor_chart_params)
        por_setor = cur.fetchall()
        tendencia_sql = "SELECT DATE_FORMAT(data_admissao, '%Y-%m') as mes, COUNT(id) as total FROM colaboradores WHERE data_admissao >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY mes ORDER BY mes ASC;"
        cur.execute(tendencia_sql)
        tendencia_contratacoes = cur.fetchall()
        table_where_clauses = base_where_clauses[:]
        table_params = base_params[:]
        table_where_clauses.append("ativo = 0" if show_inactive else "ativo = 1")
        if search_query: table_where_clauses.append("(nome LIKE %s OR cpf LIKE %s)"); table_params.extend(
            [f"%{search_query}%", f"%{search_query}%"])
        table_where_sql = " AND ".join(table_where_clauses) if table_where_clauses else "1=1"
        cur.execute(f"SELECT COUNT(*) as total FROM colaboradores WHERE {table_where_sql}", table_params)
        total_items = (cur.fetchone() or {}).get('total', 0)
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
    except mysql_errors.Error as db_err:
        return jsonify(error=f"Erro de comunicação com o banco de dados: {db_err}"), 500
    except Exception as e:
        return jsonify(error="Ocorreu um erro inesperado ao processar a solicitação."), 500
    finally:
        close_safe(conn, cur)


@admin.route('/api/colaborador/add', methods=['POST'])
def add_new_colaborator():
    if 'admin_logged_in' not in session:
        return jsonify(success=False, message="Acesso não autorizado."), 401

    conn_rh, cur_rh = None, None
    try:
        foto_filename, error_msg = process_photo(request)
        if error_msg: return jsonify(success=False, message=error_msg), 500

        # Coleta os dados do formulário
        nome = request.form.get('nome').strip().upper()
        cpf = request.form.get('cpf')
        pis_str = request.form.get('pis')
        data_nascimento = request.form.get('data_nascimento')
        cargo = request.form.get('cargo').strip().upper()
        setor = request.form.get('setor').strip().upper()
        unidade = request.form.get('unidade')
        data_admissao = request.form.get('data_admissao')

        if not all([nome, cpf, data_nascimento, cargo, setor, unidade, data_admissao]):
            return jsonify(success=False, message="Todos os campos (exceto PIS) são obrigatórios."), 400
        if not is_cpf_valid(cpf):
            return jsonify(success=False, message="O CPF informado é inválido."), 400

        # Passo 1: Inserir no banco do RH para obter a matrícula
        conn_rh = get_db_connection()
        cur_rh = conn_rh.cursor()
        cur_rh.execute("SELECT id FROM colaboradores WHERE cpf = %s", (cpf,))
        if cur_rh.fetchone():
            return jsonify(success=False, message=f"CPF '{cpf}' já está cadastrado no RH."), 409

        sql_rh = """
            INSERT INTO colaboradores (nome, cpf, pis, setor, data_nascimento, cargo, unidade, data_admissao, foto_filename, ativo, last_sync_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'pendente')
        """
        params_rh = (nome, cpf, pis_str, setor, data_nascimento, cargo, unidade, data_admissao, foto_filename)
        cur_rh.execute(sql_rh, params_rh)
        new_rh_id = cur_rh.lastrowid
        conn_rh.commit()
        print(f"INFO: Colaborador '{nome}' criado no banco do RH com ID: {new_rh_id}")

        # Passo 2: Criar o usuário diretamente na tabela 'users' do iDSecure
        idsecure_user_id, creation_error = create_idsecure_user(
            nome=nome, cpf=cpf, pis=pis_str,
            senha=data_nascimento, matricula=new_rh_id
        )
        if not idsecure_user_id:
            cur_rh.execute("UPDATE colaboradores SET last_sync_status = 'falhou_criacao' WHERE id = %s", (new_rh_id,))
            conn_rh.commit()
            return jsonify(success=False, message=f"RH: OK, mas FALHA ao criar no iDSecure: {creation_error}")

        # Passo 3: Adicionar a foto, se houver
        if foto_filename:
            photo_success, photo_error = add_photo_to_idsecure(idsecure_user_id, foto_filename)
            if not photo_success:
                cur_rh.execute(
                    "UPDATE colaboradores SET idsecure_user_id = %s, last_sync_status = 'falhou_foto' WHERE id = %s",
                    (idsecure_user_id, new_rh_id))
                conn_rh.commit()
                return jsonify(success=False, message=f"Usuário criado no iDSecure, mas FALHA na foto: {photo_error}")

        # Passo 4 (Final): Sincronizar com os equipamentos
        sync_success, sync_error = trigger_idsecure_sync(idsecure_user_id)
        if not sync_success:
            print(f"AVISO: Falha ao acionar sincronização para o usuário {idsecure_user_id}: {sync_error}")

        # Atualiza o status final no banco do RH
        final_status = 'sincronizado' if foto_filename else 'sincronizado_sem_foto'
        cur_rh.execute("UPDATE colaboradores SET idsecure_user_id = %s, last_sync_status = %s WHERE id = %s",
                       (idsecure_user_id, final_status, new_rh_id))
        conn_rh.commit()

        return jsonify(success=True, message="Colaborador sincronizado com iDSecure com sucesso!")

    except Exception as e:
        if conn_rh: conn_rh.rollback()
        return jsonify(success=False, message=f"Ocorreu um erro inesperado no servidor: {e}"), 500
    finally:
        close_safe(conn_rh, cur_rh)


@admin.route('/api/colaborador/edit/<int:colaborador_id>', methods=['POST'])
def edit_colaborador_data(colaborador_id):
    if 'admin_logged_in' not in session: return jsonify(success=False, message="Acesso não autorizado."), 401
    conn, cur = None, None
    try:
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')
        cargo = request.form.get('cargo')
        setor = request.form.get('setor')
        unidade = request.form.get('unidade')
        data_admissao = request.form.get('data_admissao')
        if not is_cpf_valid(cpf): return jsonify(success=False, message="O CPF informado é inválido."), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM colaboradores WHERE cpf = %s AND id != %s", (cpf, colaborador_id))
        if cur.fetchone():
            return jsonify(success=False, message=f"CPF '{cpf}' já pertence a outro colaborador."), 409
        sql = "UPDATE colaboradores SET nome = %s, cpf = %s, data_nascimento = %s, setor = %s, cargo = %s, unidade = %s, data_admissao = %s WHERE id = %s"
        params = (nome.strip().upper(), cpf, data_nascimento, setor.strip().upper(), cargo.strip().upper(), unidade,
                  data_admissao, colaborador_id)
        cur.execute(sql, params)
        conn.commit()
        return jsonify(success=True, message="Colaborador atualizado no sistema de RH com sucesso!")
    except Exception as e:
        if conn: conn.rollback()
        return jsonify(success=False, message=f"Ocorreu um erro ao salvar as alterações: {e}"), 500
    finally:
        close_safe(conn, cur)


@admin.route('/colaborador/toggle-status/<int:colaborador_id>', methods=['POST'])
def toggle_colaborator_status(colaborador_id):
    if 'admin_logged_in' not in session: return jsonify(success=False, message="Acesso não autorizado."), 401
    conn, cur = None, None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT nome, ativo FROM colaboradores WHERE id = %s", (colaborador_id,))
        colaborador = cur.fetchone()
        if not colaborador: return jsonify(success=False, message="Colaborador não encontrado."), 404
        new_status = 0 if colaborador['ativo'] == 1 else 1
        status_texto = "inativado" if new_status == 0 else "reativado"
        cur.execute("UPDATE colaboradores SET ativo = %s WHERE id = %s", (new_status, colaborador_id))
        conn.commit()
        return jsonify(success=True, message="Status alterado com sucesso.",
                       data={'nome': colaborador['nome'], 'status_texto': status_texto})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify(success=False, message="Erro ao alterar o status."), 500
    finally:
        close_safe(conn, cur)


@admin.route('/api/colaborador/<int:colaborador_id>', methods=['GET'])
def get_colaborador_data(colaborador_id):
    if 'admin_logged_in' not in session: return jsonify(success=False, message="Acesso não autorizado."), 401
    conn, cur = None, None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, nome, cpf, data_nascimento, setor, cargo, unidade, data_admissao FROM colaboradores WHERE id = %s",
            (colaborador_id,))
        colaborador = cur.fetchone()
        if colaborador:
            if colaborador.get('data_nascimento'): colaborador['data_nascimento'] = colaborador[
                'data_nascimento'].strftime('%Y-%m-%d')
            if colaborador.get('data_admissao'): colaborador['data_admissao'] = colaborador['data_admissao'].strftime(
                '%Y-%m-%d')
            return jsonify(success=True, data=colaborador)
        else:
            return jsonify(success=False, message="Colaborador não encontrado."), 404
    except Exception as e:
        return jsonify(success=False, message="Erro ao buscar dados."), 500
    finally:
        close_safe(conn, cur)


@admin.route('/api/export-data')
def export_data():
    if 'admin_logged_in' not in session: return "Não autorizado", 401
    conn, cur = None, None
    try:
        unidade_filtro, setor_filtro, search_query = request.args.get('unidade'), request.args.get(
            'setor'), request.args.get('search')
        show_inactive = request.args.get('inactive', 'false').lower() == 'true'
        where_clauses, params = [], []
        if unidade_filtro: where_clauses.append("unidade = %s"); params.append(unidade_filtro)
        if setor_filtro: where_clauses.append("setor = %s"); params.append(setor_filtro)
        where_clauses.append("ativo = 0" if show_inactive else "ativo = 1")
        if search_query: where_clauses.append("(nome LIKE %s OR cpf LIKE %s)"); params.extend(
            [f"%{search_query}%", f"%{search_query}%"])
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        query = f"SELECT nome, data_nascimento, cpf, setor, cargo, unidade, data_admissao FROM colaboradores WHERE {where_sql} ORDER BY nome ASC"
        cur.execute(query, params)
        df = pd.DataFrame(cur.fetchall())
        df.rename(
            columns={'nome': 'Nome Completo', 'data_nascimento': 'Data de Nascimento', 'cpf': 'CPF', 'setor': 'Setor',
                     'cargo': 'Cargo', 'unidade': 'Unidade', 'data_admissao': 'Data de Admissão'}, inplace=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Colaboradores')
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='relatorio_colaboradores.xlsx')
    except Exception as e:
        return "Erro ao gerar o relatório.", 500
    finally:
        close_safe(conn, cur)


@admin.route('/api/get-setores')
def get_all_setores():
    if 'admin_logged_in' not in session: return jsonify(error="Não autorizado"), 401
    conn, cur = None, None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT DISTINCT setor FROM colaboradores WHERE setor IS NOT NULL AND setor != '' ORDER BY setor ASC")
        return jsonify([row['setor'] for row in cur.fetchall()])
    except Exception as e:
        return jsonify([]), 500
    finally:
        close_safe(conn, cur)


@admin.route('/api/get-cargos')
def get_all_cargos():
    if 'admin_logged_in' not in session: return jsonify(error="Não autorizado"), 401
    conn, cur = None, None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT DISTINCT cargo FROM colaboradores WHERE cargo IS NOT NULL AND cargo != '' ORDER BY cargo ASC")
        return jsonify([row['cargo'] for row in cur.fetchall()])
    except Exception as e:
        return jsonify([]), 500
    finally:
        close_safe(conn, cur)


@admin.route('/fotos_colaboradores/<path:filename>')
def serve_foto_colaborador(filename):
    folder = current_app.config.get('FOTOS_FOLDER')
    if not folder: return "Pasta de fotos não configurada", 404
    return send_from_directory(folder, filename, as_attachment=False)