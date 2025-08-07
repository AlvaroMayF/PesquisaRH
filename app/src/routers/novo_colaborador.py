# src/routers/novo_colaborador.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection
import re
import os
import time
import base64

novo_colaborador_bp = Blueprint(
    'novo_colaborador',
    __name__,
    template_folder='../views'
)

# Define as extensões de arquivo permitidas para as fotos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Rota para EXIBIR a página e CRIAR um novo colaborador
@novo_colaborador_bp.route('/admin/novo-colaborador', methods=['GET', 'POST'])
def novo_colaborador_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    # Processa o formulário de CRIAÇÃO
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')

        if not nome or not cpf or not data_nascimento:
            flash('Para cadastrar, todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('novo_colaborador.novo_colaborador_view'))

        cpf_limpo = re.sub(r'[^0-9]', '', cpf)

        # --- LÓGICA PARA PROCESSAR A FOTO ---
        foto_filename = None
        foto_upload = request.files.get('foto')

        # 1. Verifica se foi enviado um arquivo via upload
        if foto_upload and foto_upload.filename != '' and allowed_file(foto_upload.filename):
            filename = secure_filename(foto_upload.filename)
            timestamp = int(time.time())
            foto_filename = f"{timestamp}_{filename}"
            save_path = os.path.join(current_app.config['FOTOS_FOLDER'], foto_filename)
            foto_upload.save(save_path)

        # 2. Se não, verifica se veio uma foto da webcam (em base64)
        elif 'foto_base64' in request.form and request.form['foto_base64']:
            try:
                img_data_str = request.form['foto_base64'].split(',')[1]
                img_data = base64.b64decode(img_data_str)

                timestamp = int(time.time())
                foto_filename = f"webcam_{timestamp}.jpg"

                save_path = os.path.join(current_app.config['FOTOS_FOLDER'], foto_filename)
                with open(save_path, 'wb') as f:
                    f.write(img_data)
            except Exception as e:
                flash(f'Erro ao processar a imagem da webcam: {e}', 'danger')
                return redirect(url_for('novo_colaborador.novo_colaborador_view'))
        # --- FIM DA LÓGICA DA FOTO ---

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            # Adiciona a coluna 'ativo' e a nova coluna 'foto_filename' no insert
            cur.execute(
                "INSERT INTO colaboradores (nome, cpf, data_nascimento, ativo, foto_filename) VALUES (%s, %s, %s, 1, %s)",
                (nome, cpf_limpo, data_nascimento, foto_filename)
            )
            conn.commit()
            cur.close()
            conn.close()
            flash(f'Colaborador "{nome}" cadastrado com sucesso!', 'success')
        except Exception as e:
            if '1062' in str(e):
                flash('Erro: Este CPF já está cadastrado no sistema.', 'danger')
            else:
                flash(f'Ocorreu um erro ao cadastrar: {e}', 'danger')

        return redirect(url_for('novo_colaborador.novo_colaborador_view'))

    # Se for método GET, apenas renderiza a página
    return render_template('NovoColaborador/NovoColaborador.html')


# --- ROTA PARA PROCESSAR A INATIVAÇÃO (SEM ALTERAÇÕES) ---
@novo_colaborador_bp.route('/admin/inativar-colaborador', methods=['POST'])
def inativar_colaborador():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    cpf_para_inativar = request.form.get('cpf_inativar')

    if not cpf_para_inativar:
        flash('Para inativar, o campo CPF é obrigatório.', 'danger')
        return redirect(url_for('novo_colaborador.novo_colaborador_view'))

    cpf_limpo = re.sub(r'[^0-9]', '', cpf_para_inativar)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Primeiro, verifica se o colaborador existe e está ativo
        cur.execute("SELECT id FROM colaboradores WHERE cpf = %s AND ativo = 1", (cpf_limpo,))
        colaborador = cur.fetchone()

        if colaborador:
            # Se existe, atualiza o status para 0 (Inativo)
            cur.execute("UPDATE colaboradores SET ativo = 0 WHERE cpf = %s", (cpf_limpo,))
            conn.commit()
            flash(f'Colaborador com CPF {cpf_para_inativar} foi inativado com sucesso.', 'success')
        else:
            flash('Nenhum colaborador ativo encontrado com este CPF.', 'danger')

        cur.close()
        conn.close()
    except Exception as e:
        flash(f'Ocorreu um erro ao inativar: {e}', 'danger')

    return redirect(url_for('novo_colaborador.novo_colaborador_view'))