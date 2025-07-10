# app/src/routers/admin_surveys.py

from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from ..config.db import get_db_connection

admin_surveys_bp = Blueprint('admin_surveys', __name__)


# Rota para listar todas as pesquisas
@admin_surveys_bp.route('/admin/gerenciar-pesquisas')
def gerenciar_pesquisas_view():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, is_active, start_date, end_date FROM surveys ORDER BY id DESC")
    surveys = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin/gerenciar_pesquisas.html', surveys=surveys)


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

    return render_template('admin/survey_form.html', survey=None)


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

    return render_template('admin/survey_form.html', survey=survey)


# Rota para gerenciar as perguntas de uma pesquisa específica
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/gerenciar-perguntas')
def gerenciar_perguntas_view(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

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
        section = question['section_title']
        if section not in grouped_questions:
            grouped_questions[section] = []
        grouped_questions[section].append(question)

    cursor.close()
    conn.close()

    return render_template('admin/manage_questions.html', survey=survey, grouped_questions=grouped_questions)


# Rota para o formulário de adicionar pergunta
@admin_surveys_bp.route('/admin/pesquisas/<int:survey_id>/perguntas/adicionar', methods=['POST'])
def adicionar_pergunta_view(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

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
            max_order = cursor.fetchone()[0]
            new_order_index = (max_order or 0) + 1

            sql_insert_question = "INSERT INTO form_questions (survey_id, question_text, question_type, section_title, order_index) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql_insert_question,
                           (survey_id, question_text, question_type, section_title, new_order_index))

            new_question_id = cursor.lastrowid

            if question_type == 'radio':
                option_texts = request.form.getlist('option_text')
                sql_insert_option = "INSERT INTO form_options (question_id, option_value, option_label) VALUES (%s, %s, %s)"

                for option_text in option_texts:
                    if option_text.strip():
                        cursor.execute(sql_insert_option, (new_question_id, option_text, option_text))

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


# Rota para deletar uma pesquisa
@admin_surveys_bp.route('/admin/deletar-pesquisa/<int:survey_id>', methods=['POST'])
def deletar_pesquisa(survey_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminLogin.admin_login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM surveys WHERE id = %s", (survey_id,))
        conn.commit()
        flash("Pesquisa excluída com sucesso.", "success")
    except Exception as e:
        flash(f"Erro ao excluir a pesquisa: {e}", "error")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return redirect(url_for('admin_surveys.gerenciar_pesquisas_view'))
