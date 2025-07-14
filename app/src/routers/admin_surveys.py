# app/src/routers/admin_surveys.py

from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from ..config.db import get_db_connection
from datetime import date

admin_surveys_bp = Blueprint('admin_surveys', __name__)


# --- FUNÇÃO AUXILIAR PARA VERIFICAR SE A PESQUISA ESTÁ CONGELADA ---
def is_survey_locked(survey_id):
    """Verifica se uma pesquisa já recebeu respostas e, portanto, deve ser congelada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM responses WHERE survey_id = %s", (survey_id,))
    response_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return response_count > 0


# Rota para listar todas as pesquisas
@admin_surveys_bp.route('/admin/gerenciar-pesquisas')
def gerenciar_pesquisas_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            s.id, s.name, s.is_active, s.start_date, s.end_date,
            (SELECT COUNT(*) FROM form_questions fq WHERE fq.survey_id = s.id) as questions_count,
            (SELECT COUNT(*) FROM responses r WHERE r.survey_id = s.id) as responses_count
        FROM surveys s 
        ORDER BY s.is_active DESC, s.id DESC
    """)
    surveys = cursor.fetchall()

    cursor.close()
    conn.close()

    today = date.today()
    for survey in surveys:
        progress_percentage = 0
        if survey.get('start_date') and survey.get('end_date') and survey['start_date'] <= survey['end_date']:
            start, end = survey['start_date'], survey['end_date']
            if today < start:
                progress_percentage = 0
            elif today > end:
                progress_percentage = 100
            else:
                total_duration = (end - start).days
                elapsed_duration = (today - start).days
                progress_percentage = (elapsed_duration / total_duration) * 100 if total_duration > 0 else 100
        survey['progress'] = max(0, min(100, progress_percentage))

    return render_template('admin/gerenciar_pesquisas.html', surveys=surveys)


# Rota para gerenciar as perguntas de uma pesquisa
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/gerenciar-perguntas')
def gerenciar_perguntas_view(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    locked = is_survey_locked(survey_id)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM surveys WHERE id = %s", (survey_id,))
    survey = cursor.fetchone()

    if not survey:
        flash("Pesquisa não encontrada.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))

    cursor.execute(
        "SELECT id, question_text, question_type, section_title, order_index FROM form_questions WHERE survey_id = %s ORDER BY order_index",
        (survey_id,)
    )
    questions = cursor.fetchall()

    grouped_questions = {}
    for question in questions:
        section_title = question.get('section_title') or "Perguntas Gerais"
        if section_title not in grouped_questions:
            grouped_questions[section_title] = []

        if question['question_type'] == 'radio':
            cursor.execute("SELECT id, option_label FROM form_options WHERE question_id = %s ORDER BY id",
                           (question['id'],))
            question['options'] = cursor.fetchall()

        grouped_questions[section_title].append(question)

    cursor.close()
    conn.close()

    return render_template('admin/manage_questions.html', survey=survey, grouped_questions=grouped_questions,
                           is_locked=locked)


# Rota para atualizar uma pergunta via AJAX
@admin_surveys_bp.route('/admin/perguntas/<int:question_id>/update', methods=['POST'])
def update_question(question_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    conn_check = get_db_connection()
    cursor_check = conn_check.cursor(dictionary=True)
    cursor_check.execute("SELECT survey_id FROM form_questions WHERE id = %s", (question_id,))
    result = cursor_check.fetchone()
    cursor_check.close()
    conn_check.close()

    if not result:
        return jsonify({'success': False, 'message': 'Pergunta não encontrada.'}), 404

    if is_survey_locked(result['survey_id']):
        return jsonify(
            {'success': False, 'message': 'Não é possível editar uma pesquisa que já possui respostas.'}), 403

    data = request.get_json()
    question_text = data.get('question_text')
    section_title = data.get('section_title')
    question_type = data.get('question_type')

    if not all([question_text, question_type]):
        return jsonify({'success': False, 'message': 'Dados incompletos.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        conn.start_transaction()
        cursor.execute(
            "UPDATE form_questions SET question_text = %s, section_title = %s, question_type = %s WHERE id = %s",
            (question_text, section_title, question_type, question_id)
        )
        if question_type == 'text':
            cursor.execute("DELETE FROM form_options WHERE question_id = %s", (question_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Pergunta atualizada!'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# Rota para o formulário de adicionar pergunta
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/perguntas/adicionar', methods=['POST'])
def adicionar_pergunta_view(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    if is_survey_locked(survey_id):
        flash("Não é possível adicionar perguntas a uma pesquisa que já possui respostas.", "error")
        return redirect(url_for('admin_surveys.gerenciar_perguntas_view', survey_id=survey_id))

    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        section_title = request.form.get('section_title')

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            conn.start_transaction()
            cursor.execute("SELECT MAX(order_index) as max_order FROM form_questions WHERE survey_id = %s",
                           (survey_id,))
            max_order_result = cursor.fetchone()
            max_order = max_order_result[0] if max_order_result else 0
            new_order_index = (max_order or 0) + 1

            sql_insert_question = "INSERT INTO form_questions (survey_id, question_text, question_type, section_title, order_index) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_insert_question,
                           (survey_id, question_text, question_type, section_title, new_order_index))
            new_question_id = cursor.lastrowid

            if question_type == 'radio':
                option_texts = request.form.getlist('option_text')
                sql_insert_option = "INSERT INTO form_options (question_id, option_value, option_label) VALUES (%s, %s, %s)"
                for option_text in option_texts:
                    if option_text and option_text.strip():
                        cursor.execute(sql_insert_option, (new_question_id, option_text.strip(), option_text.strip()))
            conn.commit()
            flash("Pergunta adicionada com sucesso!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao adicionar pergunta: {e}", "error")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        return redirect(url_for('admin_surveys.gerenciar_perguntas_view', survey_id=survey_id))


# Rota para deletar uma pergunta
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/perguntas/<int:question_id>/deletar', methods=['POST'])
def deletar_pergunta_view(survey_id, question_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    if is_survey_locked(survey_id):
        flash("Não é possível excluir perguntas de uma pesquisa que já possui respostas.", "error")
        return redirect(url_for('admin_surveys.gerenciar_perguntas_view', survey_id=survey_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM responses WHERE question_id = %s", (question_id,))
        cursor.execute("DELETE FROM form_options WHERE question_id = %s", (question_id,))
        cursor.execute("DELETE FROM form_questions WHERE id = %s", (question_id,))
        conn.commit()
        flash("Pergunta excluída com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir a pergunta: {e}", "error")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return redirect(url_for('admin_surveys.gerenciar_perguntas_view', survey_id=survey_id))


# Rota para criar uma nova pesquisa
@admin_surveys_bp.route('/admin/pesquisas/nova', methods=['GET', 'POST'])
def nova_pesquisa_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = 'is_active' in request.form
        start_date = request.form.get('start_date') or None
        end_date = request.form.get('end_date') or None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO surveys (name, description, is_active, start_date, end_date) VALUES (%s, %s, %s, %s, %s)",
                (name, description, is_active, start_date, end_date)
            )
            conn.commit()
            flash("Nova pesquisa criada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao criar pesquisa: {e}", "error")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
        return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))

    return render_template('admin/survey_form.html', survey=None, title="Criar Nova Pesquisa", action="Criar")


# Rota para editar os detalhes de uma pesquisa
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/editar', methods=['GET', 'POST'])
def editar_pesquisa_view(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = 'is_active' in request.form
        start_date = request.form.get('start_date') or None
        end_date = request.form.get('end_date') or None

        try:
            cursor.execute(
                """
                UPDATE surveys 
                SET name = %s, description = %s, is_active = %s, start_date = %s, end_date = %s
                WHERE id = %s
                """,
                (name, description, is_active, start_date, end_date, survey_id)
            )
            conn.commit()
            flash("Pesquisa atualizada com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao atualizar pesquisa: {e}", "error")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))

    cursor.execute("SELECT * FROM surveys WHERE id = %s", (survey_id,))
    survey = cursor.fetchone()
    cursor.close()
    conn.close()

    if not survey:
        flash("Pesquisa não encontrada.", "error")
        return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))

    return render_template('admin/survey_form.html', survey=survey, title="Editar Pesquisa", action="Salvar Alterações")


# Rota para deletar uma pesquisa
@admin_surveys_bp.route('/admin/deletar-pesquisa/<int:survey_id>', methods=['POST'])
def deletar_pesquisa(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM responses WHERE survey_id = %s", (survey_id,))
        cursor.execute(
            "DELETE FROM form_options WHERE question_id IN (SELECT id FROM form_questions WHERE survey_id = %s)",
            (survey_id,))
        cursor.execute("DELETE FROM form_questions WHERE survey_id = %s", (survey_id,))
        cursor.execute("DELETE FROM surveys WHERE id = %s", (survey_id,))
        conn.commit()
        flash("Pesquisa e todos os seus dados foram excluídos com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir a pesquisa: {e}", "error")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))


# --- NOVAS ROTAS PARA GERIR OPÇÕES ---

@admin_surveys_bp.route('/admin/questions/<int:question_id>/options/add', methods=['POST'])
def add_option(question_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    conn_check = get_db_connection()
    cursor_check = conn_check.cursor(dictionary=True)
    cursor_check.execute("SELECT survey_id FROM form_questions WHERE id = %s", (question_id,))
    result = cursor_check.fetchone()
    if not result or is_survey_locked(result['survey_id']):
        cursor_check.close()
        conn_check.close()
        return jsonify({'success': False, 'message': 'A pesquisa está congelada.'}), 403
    cursor_check.close()
    conn_check.close()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO form_options (question_id, option_value, option_label) VALUES (%s, %s, %s)"
        cursor.execute(sql, (question_id, 'Nova Opção', 'Nova Opção'))
        new_option_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'new_option_id': new_option_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_surveys_bp.route('/admin/options/<int:option_id>/update', methods=['POST'])
def update_option(option_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    data = request.get_json()
    new_text = data.get('text')

    if not new_text:
        return jsonify({'success': False, 'message': 'O texto da opção não pode ser vazio.'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "UPDATE form_options SET option_label = %s, option_value = %s WHERE id = %s"
        cursor.execute(sql, (new_text, new_text, option_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_surveys_bp.route('/admin/options/<int:option_id>/delete', methods=['POST'])
def delete_option(option_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question_id FROM form_options WHERE id = %s", (option_id,))
        result = cursor.fetchone()
        if result:
            question_id = result[0]
            cursor.execute("SELECT COUNT(*) FROM form_options WHERE question_id = %s", (question_id,))
            if cursor.fetchone()[0] <= 1:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'A pergunta deve ter pelo menos uma opção.'}), 400

        sql = "DELETE FROM form_options WHERE id = %s"
        cursor.execute(sql, (option_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
