# src/routers/novo_comunicado.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection

novo_comunicado_bp = Blueprint(
    'novo_comunicado',
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


@novo_comunicado_bp.route('/admin/novo-comunicado', methods=['GET', 'POST'])
def novo_comunicado_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        categoria = request.form.get('categoria')
        admin_id = session.get('admin_id', 1)

        if not titulo or not conteudo or not categoria:
            flash('Todos os campos de texto são obrigatórios.', 'danger')
            return redirect(url_for('novo_comunicado.novo_comunicado_view'))

        # Padroniza quebras de linha
        conteudo = conteudo.replace('\r\n', '\n').replace('<br>', '\n').replace('&lt;br&gt;', '\n')

        imagem_url = None
        video_url = None
        file = request.files.get('arquivo')  # Campo de upload genérico para imagem ou vídeo

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_type = get_file_type(filename)

            if file_type == 'image':
                # Salva na pasta de imagens
                upload_folder = current_app.config['UPLOAD_FOLDER_IMAGES']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file.save(os.path.join(upload_folder, filename))
                imagem_url = filename

            elif file_type == 'video':
                # Salva na pasta de vídeos
                upload_folder = current_app.config['UPLOAD_FOLDER_VIDEOS']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                file.save(os.path.join(upload_folder, filename))
                video_url = filename

            else:
                # Se o tipo de arquivo não for permitido
                flash(
                    'Tipo de arquivo não permitido. Use apenas imagens (png, jpg, gif, webp) ou vídeos (mp4, webm, ogg).',
                    'danger')
                return redirect(url_for('novo_comunicado.novo_comunicado_view'))

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # ==================================================
            # ATUALIZAÇÃO: QUERY SQL COM O NOVO CAMPO video_url
            # ==================================================
            cur.execute(
                """
                INSERT INTO comunicados 
                (titulo, conteudo, admin_id, categoria, imagem_url, video_url) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (titulo, conteudo, admin_id, categoria, imagem_url, video_url)
            )
            conn.commit()
            cur.close()
            conn.close()

            flash('Comunicado publicado com sucesso!', 'success')
            return redirect(url_for('novo_comunicado.novo_comunicado_view'))

        except Exception as e:
            flash(f'Ocorreu um erro ao publicar o comunicado: {e}', 'danger')
            current_app.logger.error(f"Erro ao publicar comunicado: {e}")
            return redirect(url_for('novo_comunicado.novo_comunicado_view'))

    admin_username = session.get('username', 'Admin')
    return render_template('NovoComunicado/NovoComunicado.html', admin_username=admin_username)