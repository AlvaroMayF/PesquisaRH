# src/routers/admin_vagas.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from ..config.db import get_db_connection

# Cria o Blueprint para o gerenciamento de vagas no painel de admin
admin_vagas_bp = Blueprint('admin_vagas', __name__, url_prefix='/admin')


# Rota principal para listar todas as vagas
@admin_vagas_bp.route('/vagas')
def gerenciar_vagas():
    # Proteção: Redireciona se não for admin
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
        return redirect(url_for('adminLogin.admin_login'))

    conn = None # Inicializa conn como None para o bloco finally
    vagas = [] # Inicializa vagas como lista vazia
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # SQL atualizado para incluir a contagem de candidaturas
        # Usamos LEFT JOIN para garantir que vagas sem candidaturas também apareçam
        # e COUNT(c.id) para contar apenas candidaturas existentes, agrupando por vaga.
        cursor.execute("""
            SELECT 
                v.id, 
                v.titulo, 
                u.nome AS nome_unidade, 
                v.status,
                COUNT(c.id) AS total_candidaturas
            FROM vagas v
            JOIN unidades u ON v.unidade_id = u.id
            LEFT JOIN candidaturas c ON v.id = c.vaga_id
            GROUP BY v.id, v.titulo, u.nome, v.status
            ORDER BY v.status DESC, v.titulo ASC
        """)
        vagas = cursor.fetchall()

    except Exception as e:
        flash(f'Erro ao carregar vagas: {e}', 'danger')
        current_app.logger.error(f"Erro ao carregar vagas no admin: {e}") # Logar o erro em ambiente de produção
    finally:
        if conn: # Garante que conn foi estabelecido antes de tentar fechar
            cursor.close()
            conn.close()

    return render_template('admin/gerenciar_vagas.html', vagas=vagas)


# Rota para o formulário de ADICIONAR ou EDITAR uma vaga
@admin_vagas_bp.route('/vagas/form', methods=['GET', 'POST'])
@admin_vagas_bp.route('/vagas/form/<int:vaga_id>', methods=['GET', 'POST'])
def form_vaga(vaga_id=None):
    if not session.get('admin_logged_in'):
        flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
        return redirect(url_for('adminLogin.admin_login'))

    conn = None # Inicializa conn como None
    vaga_para_editar = None
    unidades = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Se for um POST, estamos salvando os dados
        if request.method == 'POST':
            titulo = request.form['titulo']
            descricao = request.form['descricao']
            requisitos = request.form['requisitos']
            unidade_id = request.form['unidade_id']
            status = request.form['status']

            if vaga_id:  # Se tem ID, é um UPDATE
                cursor.execute("""
                    UPDATE vagas SET titulo=%s, descricao=%s, requisitos=%s, unidade_id=%s, status=%s
                    WHERE id=%s
                """, (titulo, descricao, requisitos, unidade_id, status, vaga_id))
                flash('Vaga atualizada com sucesso!', 'success')
            else:  # Se não tem ID, é um INSERT
                cursor.execute("""
                    INSERT INTO vagas (titulo, descricao, requisitos, unidade_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (titulo, descricao, requisitos, unidade_id, status))
                flash('Vaga criada com sucesso!', 'success')

            conn.commit()
            return redirect(url_for('admin_vagas.gerenciar_vagas'))

        # Se for um GET, estamos exibindo o formulário
        if vaga_id:  # Se tem ID, busca os dados da vaga para preencher o form
            cursor.execute("SELECT * FROM vagas WHERE id = %s", (vaga_id,))
            vaga_para_editar = cursor.fetchone()

        # Busca todas as unidades para popular o <select> do formulário
        cursor.execute("SELECT id, nome FROM unidades ORDER BY nome")
        unidades = cursor.fetchall()

    except Exception as e:
        flash(f'Erro ao carregar dados do formulário: {e}', 'danger')
        current_app.logger.error(f"Erro ao carregar formulário de vaga {vaga_id or 'nova'}: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('admin/form_vaga.html', vaga=vaga_para_editar, unidades=unidades)

# --- Exemplo de como você adicionaria uma rota para exclusão (se ainda não tiver) ---
# @admin_vagas_bp.route('/vagas/excluir/<int:vaga_id>', methods=['POST'])
# def excluir_vaga(vaga_id):
#     if not session.get('admin_logged_in'):
#         flash('Acesso não autorizado. Por favor, faça login como administrador.', 'danger')
#         return redirect(url_for('adminLogin.admin_login'))
#
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         # Considere excluir candidaturas associadas primeiro, ou definir ON DELETE CASCADE na tabela candidaturas
#         cursor.execute("DELETE FROM vagas WHERE id = %s", (vaga_id,))
#         conn.commit()
#         flash('Vaga excluída com sucesso!', 'success')
#     except Exception as e:
#         flash(f'Erro ao excluir vaga: {e}', 'danger')
#         current_app.logger.error(f"Erro ao excluir vaga {vaga_id}: {e}")
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()
#
#     return redirect(url_for('admin_vagas.gerenciar_vagas'))