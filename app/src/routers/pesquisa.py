# app/src/routers/pesquisa.py

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection

pesquisa_bp = Blueprint('pesquisa', __name__)


@pesquisa_bp.route('/pesquisa/<int:survey_id>', methods=['GET', 'POST'])
def pesquisa_view(survey_id):
    colaborador_id = session.get('colaborador_id')
    if not colaborador_id:
        flash("Sessão expirada, por favor, faça o login novamente.", "info")
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. Busca os detalhes da pesquisa
    cursor.execute("SELECT id, name, description FROM surveys WHERE id = %s AND is_active = TRUE", (survey_id,))
    survey = cursor.fetchone()

    if not survey:
        flash("Pesquisa não encontrada ou não está ativa.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

    # 2. Verifica se o colaborador já respondeu
    cursor.execute("SELECT id FROM colaborador_survey_status WHERE colaborador_id = %s AND survey_id = %s",
                   (colaborador_id, survey_id))
    if cursor.fetchone():
        flash("Você já respondeu a esta pesquisa anteriormente. Obrigado!", "info")
        cursor.close()
        conn.close()
        return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

    # 3. Lógica POST para salvar as respostas
    if request.method == 'POST':
        try:
            conn.autocommit = False
            cursor.execute("SELECT setor, cargo, unidade FROM colaboradores WHERE id = %s", (colaborador_id,))
            demographics = cursor.fetchone() or {}

            sql_insert_response = "INSERT INTO responses (survey_id, colaborador_setor, colaborador_cargo, colaborador_unidade) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_insert_response, (survey_id, demographics.get('setor'), demographics.get('cargo'),
                                                 demographics.get('unidade')))
            response_id = cursor.lastrowid

            sql_insert_answer = "INSERT INTO response_answers (response_id, question_id, answer) VALUES (%s, %s, %s)"
            for key, answer in request.form.items():
                if key.startswith('question_'):
                    question_id = int(key.replace('question_', ''))
                    cursor.execute(sql_insert_answer, (response_id, question_id, answer))

            sql_update_status = "INSERT INTO colaborador_survey_status (colaborador_id, survey_id, status) VALUES (%s, %s, 'completed')"
            cursor.execute(sql_update_status, (colaborador_id, survey_id))

            conn.commit()
            flash("Sua pesquisa foi enviada com sucesso. Obrigado pela sua participação!", "success")
        except Exception as e:
            if conn: conn.rollback()
            flash("Ocorreu um erro ao salvar sua pesquisa. Por favor, tente novamente.", "error")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

    # 4. LÓGICA GET CORRIGIDA para agrupar perguntas e opções
    cursor.execute(
        "SELECT id, question_type, section_title, question_text FROM form_questions WHERE survey_id = %s ORDER BY order_index",
        (survey_id,)
    )
    questions = cursor.fetchall()

    if not questions:
        flash("Esta pesquisa não contém perguntas.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

    # Cria o dicionário que o template espera
    grouped_questions = {}
    for q in questions:
        # Adiciona as opções diretamente no dicionário da pergunta
        if q['question_type'] == 'radio':
            cursor.execute(
                "SELECT option_value, option_label FROM form_options WHERE question_id = %s ORDER BY id",
                (q['id'],)
            )
            q['options'] = cursor.fetchall()

        # Agrupa a pergunta (já com as opções) pela seção
        section_title = q.get('section_title') or "Perguntas Gerais"
        if section_title not in grouped_questions:
            grouped_questions[section_title] = []
        grouped_questions[section_title].append(q)

    cursor.close()
    conn.close()

    # Passa o dicionário 'grouped_questions' já pronto para o template
    return render_template('pesquisa/pesquisa.html', survey=survey, grouped_questions=grouped_questions)
