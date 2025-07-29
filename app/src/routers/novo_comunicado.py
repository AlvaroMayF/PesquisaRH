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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@novo_comunicado_bp.route('/admin/novo-comunicado', methods=['GET', 'POST'])
def novo_comunicado_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        categoria = request.form.get('categoria')
        admin_id = session.get('admin_id', 1)

        conteudo = conteudo.replace('\r\n', '\n')  # Padroniza para \n
        conteudo = conteudo.replace('<br>', '\n')   # Remove qualquer <br> literal
        conteudo = conteudo.replace('&lt;br&gt;', '\n') # Remove qualquer &lt;br&gt; literal
        # ------------------------------------

        # === LINHAS DE DEBUG PÓS-LIMPEZA ===
        print(f"\nDEBUG NOVO COMUNICADO: Após a limpeza")
        print(f"  Conteúdo após limpeza (repr): {repr(conteudo)}")
        print(f"  Contém '\\n'? {'\\n' in conteudo}")
        print(f"  Contém '<br>'? {'<br>' in conteudo}")
        # === FIM DAS LINHAS DE DEBUG ===

        imagem_url = None

        if not titulo or not conteudo or not categoria:
            flash('Todos os campos de texto são obrigatórios.', 'danger')
            return redirect(url_for('novo_comunicado.novo_comunicado_view'))

        if 'imagem' in request.files:
            file = request.files['imagem']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                imagem_url = filename

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO comunicados (titulo, conteudo, admin_id, categoria, imagem_url) VALUES (%s, %s, %s, %s, %s)",
                (titulo, conteudo, admin_id, categoria, imagem_url)
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