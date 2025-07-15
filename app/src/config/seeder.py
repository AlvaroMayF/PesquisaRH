# src/config/seeder.py

from .db import get_db_connection

# Os mesmos dados que tínhamos antes
SURVEY_DATA = { "name": "Pesquisa de Clima Organizacional", "description": "Uma pesquisa para avaliar a satisfação e o engajamento dos colaboradores.", "is_active": 1, "start_date": "2025-07-01", "end_date": "2025-12-31" }
QUESTIONS_DATA = [ {"text": "Estou satisfeito(a) com meu ambiente de trabalho.", "section": "Ambiente de Trabalho"}, {"text": "A comunicação entre as equipes e a liderança é clara e eficaz.", "section": "Comunicação"}, {"text": "Sinto que meu trabalho é valorizado e reconhecido pela empresa.", "section": "Reconhecimento"}, {"text": "Tenho oportunidades claras de crescimento e desenvolvimento profissional.", "section": "Desenvolvimento"}, {"text": "Eu recomendaria esta empresa como um ótimo lugar para se trabalhar.", "section": "Engajamento"} ]
OPTIONS_DATA = [ {"label": "Discordo Totalmente", "value": "1"}, {"label": "Discordo", "value": "2"}, {"label": "Neutro", "value": "3"}, {"label": "Concordo", "value": "4"}, {"label": "Concordo Totalmente", "value": "5"} ]
ADMIN_DATA = { "username": "admin", "password": "admin" }

def seed_data():
    """
    Função que insere os dados iniciais no banco.
    Assume que está sendo executada dentro de um contexto de aplicação
    e que as tabelas já foram criadas.
    """
    db = get_db_connection()
    cursor = db.cursor()

    # Limpa dados antigos para ser re-executável
    cursor.execute("DELETE FROM response_answers;")
    cursor.execute("DELETE FROM form_options;")
    cursor.execute("DELETE FROM colaborador_survey_status;")
    cursor.execute("DELETE FROM responses;")
    cursor.execute("DELETE FROM form_questions;")
    cursor.execute("DELETE FROM surveys;")
    cursor.execute("DELETE FROM admins;")

    # Insere Admin
    cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?);", (ADMIN_DATA["username"], ADMIN_DATA["password"]))

    # Insere a Pesquisa
    cursor.execute("INSERT INTO surveys (name, description, is_active, start_date, end_date) VALUES (?, ?, ?, ?, ?);", (SURVEY_DATA["name"], SURVEY_DATA["description"], SURVEY_DATA["is_active"], SURVEY_DATA["start_date"], SURVEY_DATA["end_date"]))
    survey_id = cursor.lastrowid

    # Insere Perguntas e Opções
    for index, q_data in enumerate(QUESTIONS_DATA):
        cursor.execute("INSERT INTO form_questions (survey_id, question_text, question_type, order_index, section_title) VALUES (?, ?, ?, ?, ?);", (survey_id, q_data["text"], "likert", index + 1, q_data["section"]))
        question_id = cursor.lastrowid
        for o_data in OPTIONS_DATA:
            cursor.execute("INSERT INTO form_options (question_id, option_label, option_value) VALUES (?, ?, ?);", (question_id, o_data["label"], o_data["value"]))

    db.commit()