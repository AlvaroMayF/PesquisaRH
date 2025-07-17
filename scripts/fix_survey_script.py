# scripts/fix_survey_script.py
import os
import sys

# Adiciona a pasta raiz do projeto ao path para encontrar os módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.src.config.db import get_db_connection

# ======================================================================
# ID da pesquisa a ser corrigida. Com base no seu backup, o ID é 1.
# ======================================================================
SURVEY_ID_TO_FIX = 1

# ======================================================================
# Mapeamento completo e correto das seções, perguntas e alternativas
# do PDF para a Pesquisa de Clima Organizacional.
# ======================================================================
corrections = {
    # order_index: { "section": "...", "question": "...", "options": [...] }
    1: {"section": "Tempo de Empresa", "question": "Há quanto tempo você trabalha na Rede Hospitalar Samar?",
        "options": ["Menos de 12 meses", "De 1 ano a 2 anos", "De 3 anos a 4 anos", "Acima de 5 anos"]},
    2: {"section": "Percepção Sobre a Empresa",
        "question": "Como você avalia seu nível de satisfação com o ambiente de trabalho da empresa?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    3: {"section": "Percepção Sobre a Empresa",
        "question": "Como você avalia seu nível de satisfação com a distribuição de tarefas?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    4: {"section": "Percepção Sobre a Empresa",
        "question": "Como você avalia seu nível de satisfação sobre seu trabalho ser importante para a empresa como um todo?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    5: {"section": "Percepção Sobre a Empresa",
        "question": "Como você avalia se a empresa é um bom ambiente para trabalhar?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    6: {"section": "Relacionamento no Trabalho",
        "question": "Como você avalia a cooperação entre os setores da empresa?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    7: {"section": "Relacionamento no Trabalho",
        "question": "Como você avalia a relação de trabalho com os seus colegas?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    8: {"section": "Relacionamento no Trabalho", "question": "Como você avalia o trabalho em equipe no seu setor?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    9: {"section": "Relacionamento no Trabalho",
        "question": "Em geral, como você avalia o seu nível de motivação para vir trabalhar todos os dias?",
        "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    10: {"section": "Relacionamento com a Chefia",
         "question": "O quanto você concorda com a afirmação: Meu líder imediato me trata com respeito e consideração?",
         "options": ["Discordo totalmente", "Discordo parcialmente", "Neutro", "Concordo parcialmente",
                     "Concordo totalmente"]},
    11: {"section": "Relacionamento com a Chefia",
         "question": "Como você avalia o acompanhamento do seu líder imediato em relação aos seus resultados profissionais e desenvolvimento?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    12: {"section": "Relacionamento com a Chefia",
         "question": "Como você avalia seu nível de autonomia em relação as sugestões de novas ideias e soluções para seus superiores?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    13: {"section": "Relacionamento com a Chefia",
         "question": "Como você avalia o apoio dado pelo seu líder imediato em fazer o seu melhor todos os dias?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    14: {"section": "Relacionamento com a Chefia", "question": "Você recebe feedback com que frequência?",
         "options": ["Diariamente", "Semanalmente", "Mensalmente", "Semestralmente", "Raramente", "Nunca"]},
    15: {"section": "Comunicação no Trabalho",
         "question": "Em geral, como você avalia a clareza e objetividade das comunicações internas na Rede Hospitalar Samar?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    16: {"section": "Comunicação no Trabalho",
         "question": "Como você avalia seu nível de entendimento quando recebe informações sobre seu trabalho, mudanças, elogios ou críticas?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    17: {"section": "Comunicação no Trabalho",
         "question": "A comunicação do seu líder imediato, ocorre de forma clara e objetiva?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    18: {"section": "Comunicação no Trabalho",
         "question": "Como você avalia seu nível de satisfação das orientações recebidas no seu primeiro dia de trabalho?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    19: {"section": "Comunicação no Trabalho",
         "question": "Você considera que a comunicação sobre as políticas e diretrizes da empresa é clara e acessível?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    20: {"section": "Estrutura no Ambiente de Trabalho",
         "question": "Como você avalia a limpeza, iluminação e instalações necessárias na área onde você executa suas atividades da função?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    21: {"section": "Estrutura no Ambiente de Trabalho",
         "question": "Como você avalia os materiais e equipamentos que estão à sua disposição para desempenhar um bom trabalho?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    22: {"section": "Política Salarial e Benefícios",
         "question": "Como você avalia o seu nível de satisfação com a sua remuneração?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    23: {"section": "Política Salarial e Benefícios",
         "question": "Como você avalia o seu nível de satisfação com os benefícios que você recebe da empresa?",
         "options": ["Muito satisfeito", "Satisfeito", "Insatisfeito", "Muito insatisfeito"]},
    24: {"section": "Outros Temas",
         "question": "Você recomendaria a Rede Hospitalar Samar como uma boa empresa para se trabalhar?",
         "options": ["Sim", "Não"]},
    25: {"section": "Outros Temas", "question": "Qual dos motivos abaixo o levaria a deixar a Empresa?",
         "options": ["Ambiente de trabalho estressante", "Relacionamento insatisfatório com a liderança",
                     "Falta de crescimento profissional", "Salário e benéficos não atrativos", "Outros motivos"]},
    26: {"section": "Outros Temas",
         "question": "Você acredita que a Rede hospitalar Samar é uma empresa inclusiva para pessoas de diferentes gêneros e culturas?",
         "options": ["Concordo", "Concordo em parte", "Discordo em parte", "Dicordo"]},
    27: {"section": "Sobre a Reestruturação e Mudanças",
         "question": "Como você avalia as mudanças implementadas pela consultoria TCP nos últimos dois anos?",
         "options": ["Positivas", "Neutras", "Negativas", "Não sei opinar"]},
    28: {"section": "Sobre a Reestruturação e Mudanças",
         "question": "As mudanças trouxeram melhorias significativas para o seu setor ou área de atuação?",
         "options": ["Sim, muitas melhorias", "Sim, algumas melhorias", "Não percebo melhorias",
                     "As mudanças trouxeram mais problemas"]},
    29: {"section": "Sobre Comunicação e Transparência",
         "question": "A comunicação sobre as mudanças durante a reestruturação foi clara e eficiente?",
         "options": ["Sim, sempre clara e transparente", "Em parte, algumas informações foram confusas",
                     "Não, a comunicação foi insuficiente", "Não houve comunicação adequada"]},
    30: {"section": "Sobre Comunicação e Transparência",
         "question": "Você se sente informado sobre os objetivos e os resultados esperados da reestruturação?",
         "options": ["Sim, totalmente", "Em parte", "Não, sinto falta de informações",
                     "Não tenho conhecimento sobre os objetivos"]},
    31: {"section": "Sobre Suporte e Treinamento",
         "question": "Você recebeu treinamento adequado para se adaptar às novas práticas e processos?",
         "options": ["Sim, totalmente", "Em parte", "Não, sinto falta de treinamento",
                     "Não recebi nenhum treinamento"]},
    32: {"section": "Sobre Suporte e Treinamento",
         "question": "Você se sente preparado para lidar com as novas práticas e processos implementados?",
         "options": ["Sim, totalmente", "Em parte", "Não, sinto falta de treinamento",
                     "Não recebi nenhum treinamento"]},
}


def run_fix():
    """
    Executa a correção dos textos das perguntas, seções e opções no banco de dados.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)

        print(f"--- Iniciando a correção para a pesquisa com ID: {SURVEY_ID_TO_FIX} ---")

        # Busca todas as perguntas da pesquisa pela ordem
        cur.execute(
            "SELECT id, question_text, order_index FROM form_questions WHERE survey_id = %s ORDER BY order_index",
            (SURVEY_ID_TO_FIX,)
        )
        questions_from_db = cur.fetchall()

        if not questions_from_db:
            print(f"ERRO: Nenhuma pergunta encontrada para a pesquisa com ID {SURVEY_ID_TO_FIX}. Verifique o ID.")
            return

        # Itera sobre as perguntas do banco de dados
        for question_db in questions_from_db:
            q_id = question_db['id']
            q_order = question_db['order_index']

            # Verifica se temos uma correção para essa pergunta (baseado na ordem)
            if q_order in corrections:
                correction_data = corrections[q_order]
                new_question_text = correction_data['question']
                new_section_title = correction_data['section']

                # 1. Atualiza o texto da pergunta e a seção
                print(f"Corrigindo Pergunta {q_order} (ID do BD: {q_id})...")
                cur.execute(
                    "UPDATE form_questions SET question_text = %s, section_title = %s WHERE id = %s",
                    (new_question_text, new_section_title, q_id)
                )

                # 2. Atualiza as opções da pergunta
                if 'options' in correction_data:
                    # Busca as opções da pergunta no banco, ordenadas por ID para manter a consistência
                    cur.execute(
                        "SELECT id, option_label FROM form_options WHERE question_id = %s ORDER BY id",
                        (q_id,)
                    )
                    options_from_db = cur.fetchall()

                    new_options_labels = correction_data['options']

                    if len(options_from_db) != len(new_options_labels):
                        print(
                            f"  AVISO: A Pergunta {q_order} tem {len(options_from_db)} opções no banco, mas o PDF tem {len(new_options_labels)}. Apenas as existentes serão atualizadas.")

                    # Itera e atualiza cada opção
                    for i, option_db in enumerate(options_from_db):
                        if i < len(new_options_labels):
                            opt_id = option_db['id']
                            new_option_label = new_options_labels[i]
                            print(f"  - Corrigindo Opção ID {opt_id} para: '{new_option_label}'")
                            cur.execute(
                                "UPDATE form_options SET option_label = %s, option_value = %s WHERE id = %s",
                                (new_option_label, new_option_label, opt_id)
                            )
            else:
                # Ignora a pergunta 33 (aberta) e outras que não estão no mapeamento
                if q_order != 33:
                    print(f"AVISO: Nenhuma correção encontrada para a pergunta de ordem {q_order}. Pulando.")

        # Confirma todas as alterações no banco de dados
        conn.commit()
        print("\n--- Correção concluída com sucesso! ---")

    except Exception as e:
        if conn:
            conn.rollback()  # Desfaz as alterações em caso de erro
        print(f"\nERRO: Ocorreu um problema durante a execução. As alterações foram desfeitas. Detalhes: {e}")

    finally:
        if conn and conn.is_connected():
            cur.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")


# Executa a função principal
if __name__ == '__main__':
    run_fix()