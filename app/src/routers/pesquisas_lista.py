from flask import Blueprint, render_template, flash, redirect, url_for, session
from ..config.db import get_db_connection

pesquisas_lista_bp = Blueprint('pesquisas_lista', __name__)


@pesquisas_lista_bp.route('/pesquisas')
def lista_pesquisas_view():
    colaborador_id = session.get('colaborador_id')
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            flash("Erro ao conectar com o banco de dados.", "error")
            return redirect(url_for('home.home_view'))

        cursor = conn.cursor(dictionary=True)

        # QUERY ATUALIZADA para buscar as novas colunas
        query_surveys = """
            SELECT id, name, description, end_date 
            FROM surveys 
            WHERE is_active = TRUE
              AND (start_date IS NULL OR start_date <= CURDATE())
              AND (end_date IS NULL OR end_date >= CURDATE())
            ORDER BY name
        """
        cursor.execute(query_surveys)
        active_surveys = cursor.fetchall()

        # Busca os IDs das pesquisas que o colaborador já completou
        cursor.execute(
            "SELECT survey_id FROM colaborador_survey_status WHERE colaborador_id = %s",
            (colaborador_id,)
        )
        completed_surveys_ids = {row['survey_id'] for row in cursor.fetchall()}

        # Adiciona o status a cada pesquisa
        for survey in active_surveys:
            # --- LINHA DE DEBUG ADICIONADA AQUI ---
            print(f"DEBUG: Survey carregada: {survey}")
            # -------------------------------------
            if survey['id'] in completed_surveys_ids:
                survey['status'] = 'Respondido'
            else:
                survey['status'] = 'Pendente'

        cursor.close()

    except Exception as e:
        print(f"❌ Erro ao buscar lista de pesquisas: {e}")
        flash("Ocorreu um erro ao carregar as pesquisas disponíveis.", "error")
        return redirect(url_for('home.home_view'))
    finally:
        if conn and conn.is_connected():
            conn.close()

    return render_template(
        'pesquisas/lista_pesquisas.html',
        surveys=active_surveys
    )