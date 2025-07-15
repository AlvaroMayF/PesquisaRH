# seed.py
import os
from factory import create_app
from src.config.db import get_db_connection

# --- DADOS INICIAIS ---

# 1. A pesquisa que vamos criar
SURVEY_DATA = {
    "name": "Pesquisa de Clima Organizacional",
    "description": "Uma pesquisa para avaliar a satisfação e o engajamento dos colaboradores.",
    "is_active": 1,  # 1 para ativa, 0 para inativa
    "start_date": "2025-07-01",
    "end_date": "2025-12-31"
}

# 2. As perguntas para a pesquisa
QUESTIONS_DATA = [
    {"text": "Estou satisfeito(a) com meu ambiente de trabalho.", "section": "Ambiente de Trabalho"},
    {"text": "A comunicação entre as equipes e a liderança é clara e eficaz.", "section": "Comunicação"},
    {"text": "Sinto que meu trabalho é valorizado e reconhecido pela empresa.", "section": "Reconhecimento"},
    {"text": "Tenho oportunidades claras de crescimento e desenvolvimento profissional.", "section": "Desenvolvimento"},
    {"text": "Eu recomendaria esta empresa como um ótimo lugar para se trabalhar.", "section": "Engajamento"}
]

# 3. As opções de resposta padrão (Escala Likert)
OPTIONS_DATA = [
    {"label": "Discordo Totalmente", "value": "1"},
    {"label": "Discordo", "value": "2"},
    {"label": "Neutro", "value": "3"},
    {"label": "Concordo", "value": "4"},
    {"label": "Concordo Totalmente", "value": "5"}
]

# 4. Dados do admin padrão
ADMIN_DATA = {
    "username": "admin",
    "password": "admin"  # Lembre-se de mudar isso em um ambiente real!
}


def seed_database():
    """Popula a base de dados com dados iniciais."""
    app = create_app()
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()

        try:
            print("Populando a base de dados...")

            # -- Limpa os dados existentes para evitar duplicatas --
            # A ordem é importante por causa das chaves estrangeiras
            print("Limpeza de dados antigos...")
            cursor.execute("DELETE FROM response_answers;")
            cursor.execute("DELETE FROM form_options;")
            cursor.execute("DELETE FROM colaborador_survey_status;")
            cursor.execute("DELETE FROM responses;")
            cursor.execute("DELETE FROM form_questions;")
            cursor.execute("DELETE FROM surveys;")
            cursor.execute("DELETE FROM admins;")

            # -- Inserindo o Admin --
            print("Inserindo usuário admin...")
            cursor.execute(
                "INSERT INTO admins (username, password) VALUES (?, ?);",
                (ADMIN_DATA["username"], ADMIN_DATA["password"])
            )

            # -- Inserindo a Pesquisa (Survey) --
            print("Inserindo a pesquisa principal...")
            cursor.execute(
                "INSERT INTO surveys (name, description, is_active, start_date, end_date) VALUES (?, ?, ?, ?, ?);",
                (SURVEY_DATA["name"], SURVEY_DATA["description"], SURVEY_DATA["is_active"], SURVEY_DATA["start_date"],
                 SURVEY_DATA["end_date"])
            )
            survey_id = cursor.lastrowid  # Pega o ID da pesquisa que acabamos de criar
            print(f"Pesquisa criada com ID: {survey_id}")

            # -- Inserindo as Perguntas e suas Opções --
            print("Inserindo perguntas e opções...")
            for index, q_data in enumerate(QUESTIONS_DATA):
                # Insere a pergunta
                cursor.execute(
                    "INSERT INTO form_questions (survey_id, question_text, question_type, order_index, section_title) VALUES (?, ?, ?, ?, ?);",
                    (survey_id, q_data["text"], "likert", index + 1, q_data["section"])
                )
                question_id = cursor.lastrowid  # Pega o ID da pergunta

                # Insere as opções para essa pergunta
                for o_data in OPTIONS_DATA:
                    cursor.execute(
                        "INSERT INTO form_options (question_id, option_label, option_value) VALUES (?, ?, ?);",
                        (question_id, o_data["label"], o_data["value"])
                    )

            # -- Salva todas as alterações --
            db.commit()
            print("\n✅ Sucesso! O banco de dados foi populado.")

        except Exception as e:
            db.rollback()  # Desfaz tudo se der algum erro
            print(f"\n❌ Erro ao popular o banco de dados: {e}")
        finally:
            db.close()


if __name__ == '__main__':
    seed_database()