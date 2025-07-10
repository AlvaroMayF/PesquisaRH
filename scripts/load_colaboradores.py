# scripts/load_colaboradores.py
import os
import sys
import pandas as pd
from mysql.connector import IntegrityError

# --- INÍCIO DO CÓDIGO DE AJUSTE DE CAMINHO ---
# Este bloco "ensina" o script a encontrar a pasta 'app' e seus módulos
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)
# --- FIM DO CÓDIGO DE AJUSTE DE CAMINHO ---

# Agora que o caminho do projeto é conhecido, este import funcionará
from app.src.config.db import get_db_connection

# --- CAMINHO ATUALIZADO PARA A PLANILHA ---
EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'colaboradores_samar.xlsx')


def main():
    # 1) Carrega a planilha, especificando a aba "Sheet1"
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name='Sheet1')
        print("✅ Planilha carregada com sucesso da aba 'Sheet1'.")
    except FileNotFoundError:
        print(f"❌ ERRO: Arquivo não encontrado no caminho: {EXCEL_PATH}")
        print(
            "Verifique se o nome do arquivo e a estrutura de pastas ('data/colaboradores_samar.xlsx') estão corretos.")
        return
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        return

    # Imprime os nomes das colunas encontradas para verificação
    print("\nColunas encontradas na planilha:")
    print(df.columns.tolist())
    print("-" * 30)

    # 2) Conecta ao banco
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()

    # 3) Loop e UPSERT (Update + Insert)
    print("Iniciando a atualização/inserção de colaboradores...")
    for _, row in df.iterrows():
        try:
            # Pega os dados da linha de forma segura, usando .get() que retorna None se a coluna não existir
            nome = row.get('NOME')
            data_nasc = row.get('Data de Nascimento')
            cpf_raw = row.get('CPF')

            if not all([nome, data_nasc, cpf_raw]):
                print(f"⚠️ Linha pulada por falta de dados essenciais (Nome, Data de Nascimento ou CPF).")
                continue

            # Limpa e formata o CPF para garantir que tenha 11 dígitos
            cpf = ''.join(filter(str.isdigit, str(cpf_raw).replace('.0', ''))).zfill(11)

            # Pega os dados opcionais, tratando valores nulos do pandas (NaN)
            setor = row.get('SETOR')
            setor = setor if pd.notna(setor) else None

            cargo = row.get('CARGO')
            cargo = cargo if pd.notna(cargo) else None

            unidade = row.get('UNIDADE')
            unidade = unidade if pd.notna(unidade) else None

            # SQL para inserir um novo colaborador ou atualizar um existente se o CPF já existir
            sql_upsert = """
                INSERT INTO colaboradores (cpf, nome, data_nascimento, setor, cargo, unidade)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    nome = VALUES(nome),
                    data_nascimento = VALUES(data_nascimento),
                    setor = VALUES(setor),
                    cargo = VALUES(cargo),
                    unidade = VALUES(unidade);
            """
            cursor.execute(sql_upsert, (cpf, nome, data_nasc, setor, cargo, unidade))

        except Exception as e:
            print(f"❌ Erro ao processar a linha para o nome '{row.get('NOME', 'N/A')}': {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ Importação e atualização de colaboradores concluída com sucesso.")


if __name__ == "__main__":
    main()