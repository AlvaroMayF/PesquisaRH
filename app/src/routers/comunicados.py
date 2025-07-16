# src/routers/comunicados.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection
import locale
from collections import defaultdict  # <<< ADIÇÃO IMPORTANTE

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Aviso: Locale 'pt_BR' não pôde ser configurado.")

comunicados_bp = Blueprint(
    'comunicados',
    __name__,
    template_folder='../views'
)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ROTA PARA LISTAR TODOS OS COMUNICADOS (ATUALIZADA)
@comunicados_bp.route('/comunicados')
def view_comunicados():
    comunicados = []
    feriados_por_unidade = defaultdict(list)

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # 1. Buscar os comunicados (lógica original)
        query_comunicados = """
            SELECT 
                c.id, c.titulo, c.conteudo, c.data_publicacao, 
                c.categoria, c.imagem_url, a.username AS autor
            FROM comunicados c
            JOIN admins a ON c.admin_id = a.id
            ORDER BY c.data_publicacao DESC
        """
        cur.execute(query_comunicados)
        comunicados = cur.fetchall()

        # 2. Buscar os feriados (nova lógica)
        query_feriados = 'SELECT data, descricao, unidade FROM feriados ORDER BY data'
        cur.execute(query_feriados)
        feriados_db = cur.fetchall()
        # 3. Fechar a conexão com o banco
        cur.close()
        conn.close()

        # 4. Processar os dados dos feriados para o template
        for feriado in feriados_db:
            feriados_por_unidade[feriado['unidade']].append(feriado)

    except Exception as e:
        print(f"Erro ao buscar dados da página de comunicados: {e}")
        # Em caso de erro, as variáveis já foram inicializadas como listas vazias
        # Em caso de erro, as variáveis já foram inicializadas como listas vazias

    # 5. Renderizar o template passando ambas as variáveis
    return render_template(
        'Comunicados/comunicados.html',
        comunicados=comunicados,
        feriados_por_unidade=feriados_por_unidade
    )


# ROTA PARA EXCLUIR UM COMUNICADO
@comunicados_bp.route('/admin/excluir-comunicado/<int:comunicado_id>', methods=['POST'])
def excluir_comunicado(comunicado_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT imagem_url FROM comunicados WHERE id = %s", (comunicado_id,))
        comunicado = cur.fetchone()
        if comunicado and comunicado['imagem_url']:
            caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], comunicado['imagem_url'])
            if os.path.exists(caminho_imagem):
                os.remove(caminho_imagem)

        cur.execute("DELETE FROM comunicados WHERE id = %s", (comunicado_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('Comunicado excluído com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao excluir o comunicado: {e}', 'danger')

    return redirect(url_for('comunicados.view_comunicados'))


# ROTA PARA EDITAR UM COMUNICADO
@comunicados_bp.route('/admin/editar-comunicado/<int:comunicado_id>', methods=['GET', 'POST'])
def editar_comunicado(comunicado_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        categoria = request.form.get('categoria')

        cur.execute("SELECT imagem_url FROM comunicados WHERE id = %s", (comunicado_id,))
        imagem_antiga = cur.fetchone()['imagem_url']
        imagem_url = imagem_antiga

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '' and allowed_file(file.filename):
                if imagem_antiga and os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_antiga)):
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], imagem_antiga))

                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                imagem_url = filename

        try:
            cur.execute("""
                UPDATE comunicados 
                SET titulo = %s, conteudo = %s, categoria = %s, imagem_url = %s
                WHERE id = %s
            """, (titulo, conteudo, categoria, imagem_url, comunicado_id))
            conn.commit()
            flash('Comunicado atualizado com sucesso!', 'success')
            return redirect(url_for('comunicados.view_comunicados'))
        except Exception as e:
            flash(f'Erro ao atualizar o comunicado: {e}', 'danger')

    cur.execute("SELECT * FROM comunicados WHERE id = %s", (comunicado_id,))
    comunicado = cur.fetchone()
    cur.close()
    conn.close()

    if not comunicado:
        flash('Comunicado não encontrado.', 'danger')
        return redirect(url_for('comunicados.view_comunicados'))

    admin_username = session.get('username', 'Admin')
    return render_template('comunicados/editar_comunicado.html', comunicado=comunicado, admin_username=admin_username)
