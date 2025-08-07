# src/routers/comunicados.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection
from collections import defaultdict
import locale

# Configuração de locale para datas em português
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

# ==================================================
# ATUALIZAÇÃO: DEFINIÇÃO DE ARQUIVOS PERMITIDOS
# ==================================================
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg'}


def get_file_type(filename):
    """Verifica a extensão do arquivo e retorna seu tipo ('image', 'video', ou None)."""
    if '.' not in filename:
        return None

    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    return None


# ROTA PARA LISTAR TODOS OS COMUNICADOS (ATUALIZADA)
@comunicados_bp.route('/comunicados')
def view_comunicados():
    comunicados = []
    feriados_por_unidade = defaultdict(list)

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # 1. Buscar os comunicados, incluindo o novo campo 'video_url'
        query_comunicados = """
            SELECT 
                c.id, c.titulo, c.conteudo, c.data_publicacao, 
                c.categoria, c.imagem_url, c.video_url,  -- <<< CAMPO ADICIONADO
                a.username AS autor
            FROM comunicados c
            JOIN admins a ON c.admin_id = a.id
            ORDER BY c.data_publicacao DESC
        """
        cur.execute(query_comunicados)
        comunicados = cur.fetchall()

        # 2. Buscar os feriados
        query_feriados = 'SELECT data, descricao, unidade FROM feriados ORDER BY data'
        cur.execute(query_feriados)
        feriados_db = cur.fetchall()

        cur.close()
        conn.close()

        # 3. Processar os dados dos feriados
        for feriado in feriados_db:
            feriados_por_unidade[feriado['unidade']].append(feriado)

    except Exception as e:
        flash(f"Ocorreu um erro ao buscar os dados da página: {e}", "danger")
        current_app.logger.error(f"Erro ao buscar dados da página de comunicados: {e}")

    return render_template(
        'Comunicados/comunicados.html',
        comunicados=comunicados,
        feriados_por_unidade=feriados_por_unidade
    )


# ROTA PARA EXCLUIR UM COMUNICADO (ATUALIZADA)
@comunicados_bp.route('/admin/excluir-comunicado/<int:comunicado_id>', methods=['POST'])
def excluir_comunicado(comunicado_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        # Buscar ambos os campos de mídia para exclusão do arquivo
        cur.execute("SELECT imagem_url, video_url FROM comunicados WHERE id = %s", (comunicado_id,))
        comunicado = cur.fetchone()

        if comunicado:
            # Exclui a imagem, se existir
            if comunicado['imagem_url']:
                caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGES'], comunicado['imagem_url'])
                if os.path.exists(caminho_imagem):
                    os.remove(caminho_imagem)

            # Exclui o vídeo, se existir
            if comunicado['video_url']:
                caminho_video = os.path.join(current_app.config['UPLOAD_FOLDER_VIDEOS'], comunicado['video_url'])
                if os.path.exists(caminho_video):
                    os.remove(caminho_video)

        # Exclui o registro do banco de dados
        cur.execute("DELETE FROM comunicados WHERE id = %s", (comunicado_id,))
        conn.commit()
        cur.close()
        conn.close()
        flash('Comunicado excluído com sucesso.', 'success')
    except Exception as e:
        flash(f'Erro ao excluir o comunicado: {e}', 'danger')
        current_app.logger.error(f"Erro ao excluir o comunicado: {e}")

    return redirect(url_for('comunicados.view_comunicados'))


# ROTA PARA EDITAR UM COMUNICADO (ATUALIZADA)
@comunicados_bp.route('/admin/editar-comunicado/<int:comunicado_id>', methods=['GET', 'POST'])
def editar_comunicado(comunicado_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Busca o comunicado para exibir no formulário GET
    cur.execute("SELECT * FROM comunicados WHERE id = %s", (comunicado_id,))
    comunicado = cur.fetchone()

    if not comunicado:
        flash('Comunicado não encontrado.', 'danger')
        cur.close()
        conn.close()
        return redirect(url_for('comunicados.view_comunicados'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        categoria = request.form.get('categoria')

        imagem_url = comunicado['imagem_url']
        video_url = comunicado['video_url']

        file = request.files.get('arquivo')

        # Se um novo arquivo foi enviado
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_type = get_file_type(filename)

            if not file_type:
                flash('Tipo de arquivo não permitido.', 'danger')
                cur.close()
                conn.close()
                return redirect(request.url)

            # Remover mídia antiga (imagem e vídeo) para evitar arquivos órfãos
            if comunicado['imagem_url']:
                old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER_IMAGES'], comunicado['imagem_url'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            if comunicado['video_url']:
                old_video_path = os.path.join(current_app.config['UPLOAD_FOLDER_VIDEOS'], comunicado['video_url'])
                if os.path.exists(old_video_path):
                    os.remove(old_video_path)

            # Salvar novo arquivo e atualizar as variáveis
            if file_type == 'image':
                upload_folder = current_app.config['UPLOAD_FOLDER_IMAGES']
                file.save(os.path.join(upload_folder, filename))
                imagem_url = filename
                video_url = None  # Garante que não haverá link de vídeo
            elif file_type == 'video':
                upload_folder = current_app.config['UPLOAD_FOLDER_VIDEOS']
                file.save(os.path.join(upload_folder, filename))
                video_url = filename
                imagem_url = None  # Garante que não haverá link de imagem

        try:
            # Atualiza o registro no banco de dados com os novos dados
            cur.execute("""
                UPDATE comunicados 
                SET titulo = %s, conteudo = %s, categoria = %s, imagem_url = %s, video_url = %s
                WHERE id = %s
            """, (titulo, conteudo, categoria, imagem_url, video_url, comunicado_id))
            conn.commit()
            flash('Comunicado atualizado com sucesso!', 'success')
            return redirect(url_for('comunicados.view_comunicados'))
        except Exception as e:
            flash(f'Erro ao atualizar o comunicado: {e}', 'danger')
            current_app.logger.error(f"Erro ao atualizar o comunicado: {e}")
        finally:
            cur.close()
            conn.close()

    # Se for um GET, apenas renderiza a página de edição
    admin_username = session.get('username', 'Admin')
    # O fechamento da conexão foi movido para dentro dos blocos lógicos
    if conn.is_connected():
        cur.close()
        conn.close()
    return render_template('Comunicados/editar_comunicado.html', comunicado=comunicado, admin_username=admin_username)