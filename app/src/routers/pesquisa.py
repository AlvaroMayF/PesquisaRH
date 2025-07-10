from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..config.db import get_db_connection

pesquisa = Blueprint('pesquisa', __name__)


@pesquisa.route('/pesquisa/<int:survey_id>', methods=['GET', 'POST'])
def pesquisa_view(survey_id):
    colaborador_id = session.get('colaborador_id')

    # --- LÓGICA DE SALVAR RESPOSTAS (POST) ---
    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                flash("Erro de conexão com o banco de dados.", "error")
                return redirect(url_for('home.home_view'))

            # AJUSTE IMPORTANTE: Controlamos o commit manualmente
            conn.autocommit = False
            cursor = conn.cursor(dictionary=True)

            # Busca os dados demográficos
            cursor.execute("SELECT setor, cargo, unidade FROM colaboradores WHERE id = %s", (colaborador_id,))
            demographics = cursor.fetchone() or {}
            colaborador_setor = demographics.get('setor')
            colaborador_cargo = demographics.get('cargo')
            colaborador_unidade = demographics.get('unidade')

            # 1. Inserindo na tabela 'responses'
            sql_insert_response = "INSERT INTO responses (survey_id, colaborador_setor, colaborador_cargo, colaborador_unidade) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql_insert_response, (survey_id, colaborador_setor, colaborador_cargo, colaborador_unidade))
            response_id = cursor.lastrowid

            # 2. Inserindo na tabela 'response_answers'
            for key, answer in request.form.items():
                if key.startswith('resposta'):
                    question_id = int(key.replace('resposta', ''))
                    sql_insert_answer = "INSERT INTO response_answers (response_id, question_id, answer) VALUES (%s, %s, %s)"
                    cursor.execute(sql_insert_answer, (response_id, question_id, answer))

            # 3. Inserindo na tabela 'colaborador_survey_status'
            sql_update_status = "INSERT INTO colaborador_survey_status (colaborador_id, survey_id, status) VALUES (%s, %s, 'completed')"
            cursor.execute(sql_update_status, (colaborador_id, survey_id))

            # 4. Se tudo deu certo, salva todas as alterações de uma vez
            conn.commit()
            flash("Sua pesquisa foi enviada com sucesso. Obrigado pela sua participação!", "success")

        except Exception as e:
            if conn:
                conn.rollback()  # Desfaz tudo se houver qualquer erro
            print(f"❌ Erro ao salvar a pesquisa: {e}")
            flash("Ocorreu um erro ao salvar sua pesquisa. Por favor, tente novamente.", "error")

        finally:
            if conn and conn.is_connected():
                if cursor:
                    cursor.close()
                conn.close()

        return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

    # --- Lógica GET para exibir o formulário (continua a mesma) ---
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM colaborador_survey_status WHERE colaborador_id = %s AND survey_id = %s",
                       (colaborador_id, survey_id))
        if cursor.fetchone():
            flash("Você já respondeu a esta pesquisa anteriormente. Obrigado!", "info")
            return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

        # O resto do seu código GET para buscar as perguntas continua o mesmo...
        cursor.execute(
            "SELECT id, question_type, section_title, question_text FROM form_questions WHERE survey_id = %s ORDER BY order_index",
            (survey_id,))
        questions = cursor.fetchall()

        if not questions:
            flash("Esta pesquisa não foi encontrada ou não contém perguntas.", "error")
            return redirect(url_for('pesquisas_lista.lista_pesquisas_view'))

        question_ids = [q['id'] for q in questions]
        options = {}
        if question_ids:
            format_strings = ','.join(['%s'] * len(question_ids))
            cursor.execute(
                f"SELECT question_id, option_value, option_label AS option_text FROM form_options WHERE question_id IN ({format_strings}) ORDER BY id",
                tuple(question_ids))
            all_options = cursor.fetchall()

            for opt in all_options:
                q_id = opt['question_id']
                if q_id not in options:
                    options[q_id] = []
                options[q_id].append(opt)

    except Exception as e:
        print(f"❌ Erro ao buscar dados da pesquisa: {e}")
        flash("Ocorreu um erro ao carregar a pesquisa. Tente novamente.", "error")
        return redirect(url_for('home.home_view'))
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()

    return render_template('pesquisa/pesquisa.html', questions=questions, options=options)