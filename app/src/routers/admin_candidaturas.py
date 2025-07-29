# src/routers/admin_candidaturas.py

from flask import Blueprint, render_template, request, send_from_directory, flash, redirect, url_for, session, \
    current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection
import os
import datetime  # Para formatar a data da candidatura no template

# Cria o Blueprint para o gerenciamento de candidaturas no painel de admin
admin_candidaturas_bp = Blueprint('admin_candidaturas', __name__, url_prefix='/admin/candidaturas')

# Diretório onde os currículos estão armazenados
# Garanta que este diretório existe e que o servidor tem permissões de escrita
UPLOAD_FOLDER = 'uploads/curriculos'


@admin_candidaturas_bp.route('/')
def gerenciar_candidaturas():
    """
    Exibe a lista de candidaturas. Permite filtros e pesquisa.
    Pode ser filtrado por vaga_id.
    """
    # Proteção: Redireciona se não for admin
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
        return redirect(url_for('adminLogin.admin_login'))

    conn = None
    candidaturas = []

    # Parâmetros de filtro/pesquisa
    status_filtro = request.args.get('status', default='Todas')
    termo_busca = request.args.get('busca', default='')
    vaga_id_filtro = request.args.get('vaga_id', default=None, type=int)  # Novo: ID da vaga para filtro

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql_query = """
            SELECT c.id, c.nome_completo, c.email, c.telefone, c.tipo_candidatura,
                   c.nome_indicador, c.arquivo_curriculo, c.status, c.data_candidatura,
                   v.titulo AS titulo_vaga, u.nome AS nome_unidade
            FROM candidaturas c
            JOIN vagas v ON c.vaga_id = v.id
            JOIN unidades u ON v.unidade_id = u.id
            WHERE 1=1
        """
        params = []

        if status_filtro != 'Todas':
            sql_query += " AND c.status = %s"
            params.append(status_filtro)

        if termo_busca:
            termo_busca_like = f"%{termo_busca}%"
            sql_query += " AND (c.nome_completo LIKE %s OR v.titulo LIKE %s OR u.nome LIKE %s)"
            params.extend([termo_busca_like, termo_busca_like, termo_busca_like])

        if vaga_id_filtro:
            sql_query += " AND c.vaga_id = %s"
            params.append(vaga_id_filtro)

        sql_query += " ORDER BY c.data_candidatura DESC"

        cursor.execute(sql_query, tuple(params))
        candidaturas = cursor.fetchall()

    except Exception as e:
        flash(f'Erro ao carregar candidaturas: {e}', 'danger')
        current_app.logger.error(f"Erro ao carregar candidaturas no admin: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

    # Passa o vaga_id_filtro para o template manter o filtro ativo no dropdown, se houver
    return render_template('admin/gerenciar_candidaturas.html',
                           candidaturas=candidaturas,
                           status_filtro=status_filtro,
                           termo_busca=termo_busca,
                           vaga_id_filtro=vaga_id_filtro,  # Passa o ID da vaga filtrada
                           status_opcoes=['Todas', 'Nova', 'Em Analise', 'Aprovada', 'Rejeitada'])


@admin_candidaturas_bp.route('/<int:candidatura_id>/status', methods=['POST'])
def atualizar_status_candidatura(candidatura_id):
    """
    Atualiza o status de uma candidatura.
    """
    # Proteção: Redireciona se não for admin
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
        return redirect(url_for('adminLogin.admin_login'))

    novo_status = request.form.get('status')
    if not novo_status or novo_status not in ['Nova', 'Em Analise', 'Aprovada', 'Rejeitada']:
        flash('Status inválido.', 'danger')
        return redirect(url_for('admin_candidaturas.gerenciar_candidaturas'))

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE candidaturas SET status = %s WHERE id = %s",
            (novo_status, candidatura_id)
        )
        conn.commit()
        flash('Status da candidatura atualizado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar status: {e}', 'danger')
        current_app.logger.error(f"Erro ao atualizar status da candidatura {candidatura_id}: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

    # Redireciona de volta para a tela de gerenciamento, mantendo os filtros se possível
    query_params = request.args.to_dict()
    return redirect(url_for('admin_candidaturas.gerenciar_candidaturas', **query_params))


@admin_candidaturas_bp.route('/download/<filename>')
def download_curriculo(filename):
    """
    Permite o download de um currículo.
    Atenção: Esta rota DEVE ser protegida por autenticação de admin!
    """
    # Proteção: Redireciona se não for admin
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
        return redirect(url_for('adminLogin.admin_login'))

    try:
        # Caminho absoluto para a pasta de uploads
        full_upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)

        # Validar o filename para evitar ataques de caminho
        safe_filename = secure_filename(filename)

        # É crucial que o filename no BD seja o secure_filename
        # Verificar se o arquivo existe no caminho esperado
        if not os.path.exists(os.path.join(full_upload_path, safe_filename)):
            flash("Arquivo de currículo não encontrado.", "danger")
            # Logar para depuração: current_app.logger.warning(f"Arquivo não encontrado para download: {safe_filename}")
            return redirect(url_for('admin_candidaturas.gerenciar_candidaturas'))

        # Retorna o arquivo para download
        return send_from_directory(full_upload_path, safe_filename, as_attachment=True)
    except Exception as e:
        flash(f'Erro ao baixar currículo: {e}', 'danger')
        current_app.logger.error(f"Erro ao baixar currículo {filename}: {e}")
        return redirect(url_for('admin_candidaturas.gerenciar_candidaturas'))