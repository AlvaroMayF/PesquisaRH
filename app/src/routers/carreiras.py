# src/routers/carreiras.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from ..config.db import get_db_connection
import os  # Importar o módulo os
import time

carreiras_bp = Blueprint('carreiras', __name__)

# Configuração do diretório de uploads
# Certifique-se de que este diretório existe e tem permissões de escrita
UPLOAD_FOLDER = 'uploads/curriculos'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}  # Tipos de arquivo permitidos


# Função auxiliar para verificar extensões permitidas
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@carreiras_bp.route('/carreiras', methods=['GET', 'POST'])  # Adicionar POST
def index():
    """
    Exibe a página de carreiras com um filtro de unidades e processa candidaturas.
    """
    if request.method == 'POST':
        # Lógica para processar a candidatura
        try:
            vaga_id = request.form.get('vaga_id', type=int)
            nome_completo = request.form.get('nome_completo')
            email = request.form.get('email')
            telefone = request.form.get('telefone')
            tipo_candidatura = request.form.get('tipo_candidatura')
            nome_indicador = request.form.get('nome_indicador') if tipo_candidatura == 'Indicacao' else None

            # Validação básica
            if not all([vaga_id, nome_completo, email, tipo_candidatura]):
                flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
                return redirect(url_for('carreiras.index'))

            # Validação do arquivo de currículo
            if 'curriculo' not in request.files:
                flash('Nenhum arquivo de currículo foi enviado.', 'danger')
                return redirect(url_for('carreiras.index'))

            file = request.files['curriculo']
            if file.filename == '':
                flash('Nenhum arquivo de currículo selecionado.', 'danger')
                return redirect(url_for('carreiras.index'))

            if file and allowed_file(file.filename):
                # Garante que o diretório de uploads existe
                upload_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                os.makedirs(upload_path, exist_ok=True)

                filename = secure_filename(file.filename)
                # Adiciona um timestamp ao nome do arquivo para evitar colisões
                timestamp = str(int(request.date.timestamp())) if request.date else str(int(time.time()))
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(upload_path, unique_filename)
                file.save(file_path)

                # Salvar no banco de dados
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO candidaturas (vaga_id, nome_completo, email, telefone, tipo_candidatura, nome_indicador, arquivo_curriculo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (vaga_id, nome_completo, email, telefone, tipo_candidatura, nome_indicador, unique_filename)
                )
                conn.commit()
                cursor.close()
                conn.close()

                flash('Sua candidatura foi enviada com sucesso!', 'success')
                # Opcional: Enviar notificação para o RH (apenas o link para a nova tela de gerenciamento)
                # Aqui você integraria sua lógica de envio de e-mail ou notificação
                # ex: send_rh_notification(vaga_id, nome_completo, unique_filename)

            else:
                flash('Tipo de arquivo não permitido. Por favor, envie PDF, DOC ou DOCX.', 'danger')

            return redirect(url_for('carreiras.index'))

        except Exception as e:
            flash(f'Ocorreu um erro ao processar sua candidatura: {e}', 'danger')
            current_app.logger.error(f"Erro ao processar candidatura: {e}")  # Logar o erro
            return redirect(url_for('carreiras.index'))

    # Lógica GET existente para exibir vagas
    vagas_por_unidade = {}
    unidades_para_filtro = []

    unidade_selecionada_id = request.args.get('unidade', default=None, type=int)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, nome FROM unidades ORDER BY nome")
        unidades_para_filtro = cursor.fetchall()

        unidades_a_exibir = unidades_para_filtro
        if unidade_selecionada_id:
            unidades_a_exibir = [u for u in unidades_para_filtro if u['id'] == unidade_selecionada_id]

        for unidade in unidades_a_exibir:
            vagas_por_unidade[unidade['nome']] = []

        sql_vagas_abertas = """
            SELECT v.id, v.titulo, v.descricao, v.requisitos, u.nome AS nome_unidade
            FROM vagas v
            JOIN unidades u ON v.unidade_id = u.id
            WHERE v.status = 'Aberta'
        """
        params = []
        if unidade_selecionada_id:
            sql_vagas_abertas += " AND v.unidade_id = %s"
            params.append(unidade_selecionada_id)

        sql_vagas_abertas += " ORDER BY u.nome, v.titulo"

        cursor.execute(sql_vagas_abertas, tuple(params))
        vagas_abertas = cursor.fetchall()

        for vaga in vagas_abertas:
            if vaga['nome_unidade'] in vagas_por_unidade:
                vagas_por_unidade[vaga['nome_unidade']].append(vaga)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Erro ao buscar vagas: {e}")
        flash(f"Erro ao carregar vagas: {e}", 'danger')  # Adicionar flash message para erros na busca

    return render_template(
        'carreiras/carreiras.html',
        vagas_por_unidade=vagas_por_unidade,
        unidades=unidades_para_filtro,
        unidade_selecionada=unidade_selecionada_id
    )