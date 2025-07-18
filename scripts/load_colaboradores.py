import os
import pandas as pd
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.src.config.db import get_db_connection

# Aponta para o arquivo que foi enriquecido com as datas
EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'colaboradores_samar.xlsx')


def main():
    try:
        df = pd.read_excel(EXCEL_PATH)
        print("✅ Planilha carregada com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        print(f"Verifique se o nome do arquivo em EXCEL_PATH ('{os.path.basename(EXCEL_PATH)}') está correto.")
        return

    conn = get_db_connection()
    if not conn:
        print("❌ Falha ao conectar ao banco de dados.")
        return
    cursor = conn.cursor()

    print("Limpando a tabela 'colaboradores' existente...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE colaboradores;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Tabela limpa com sucesso.")

    print(f"Iniciando a inserção de {len(df)} colaboradores...")
    for _, row in df.iterrows():
        try:
            # Lendo os dados do Excel (usando os nomes exatos das colunas da planilha)
            nome_excel = row['NOME']
            data_nasc_excel = row['Data de Nascimento']
            cpf_excel = str(row['CPF']).replace('.0', '')
            cpf_excel = ''.join(filter(str.isdigit, cpf_excel)).zfill(11)

            setor_excel = row['SETOR'] if pd.notna(row['SETOR']) else None
            cargo_excel = row['CARGO'] if pd.notna(row['CARGO']) else None
            unidade_excel = row['UNIDADE'] if pd.notna(row['UNIDADE']) else None
            data_adm_excel = row['Admissão'] if pd.notna(row['Admissão']) else None

            # ========== CORREÇÃO PRINCIPAL NA QUERY SQL ==========
            # Os nomes das colunas na query agora correspondem EXATAMENTE aos da tabela no banco de dados.
            # `Data de Nascimento` foi trocado por `data_nascimento`.
            # Os outros nomes foram padronizados para minúsculas por segurança.
            sql_insert = """
                INSERT INTO colaboradores (
                    nome, data_nascimento, cpf, setor, cargo, unidade, data_admissao, ativo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """

            # A ordem dos parâmetros deve corresponder à ordem das colunas no INSERT
            params = (
                nome_excel,
                data_nasc_excel,
                cpf_excel,
                setor_excel,
                cargo_excel,
                unidade_excel,
                data_adm_excel
            )

            cursor.execute(sql_insert, params)

        except KeyError as e:
            print(
                f"❌ Erro de Coluna (KeyError) ao processar a linha para '{row.get('NOME', 'N/A')}'. A coluna {e} não foi encontrada no Excel.")
            print("   Verifique se todos os nomes de coluna no script correspondem aos da planilha.")
            conn.rollback()
            break
        except Exception as e:
            print(f"❌ Erro ao processar a linha para o nome '{row.get('NOME', 'N/A')}': {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Inserção de colaboradores concluída com sucesso.")


if __name__ == "__main__":
    main()