# scripts/load_colaboradores.py
import os
import pandas as pd
from app.src.config.db import get_db_connection

# ATENÇÃO: Verifique se este é o nome correto do seu novo arquivo Excel
# O nome do arquivo deve corresponder ao que você tem na pasta /data
EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'colaboradores_samar.xlsx')


def main():
    # 1) Carrega a planilha, especificando a aba "Página1"
    try:
        # Usamos a aba 'Página1' que contém todas as colunas
        df = pd.read_excel(EXCEL_PATH, sheet_name='Página1')
        print("✅ Planilha carregada com sucesso da aba 'Página1'.")
    except Exception as e:
        print(f"❌ Erro ao carregar a planilha: {e}")
        print("Verifique se o nome do arquivo em EXCEL_PATH está correto e se a aba 'Página1' existe.")
        return

    # 2) Conecta ao banco
    conn = get_db_connection()
    if not conn:
        print("❌ Falha ao conectar ao banco de dados.")
        return
    cursor = conn.cursor()

    # 3) Loop e UPSERT (Update + Insert)
    print("Iniciando a atualização/inserção de colaboradores...")
    for _, row in df.iterrows():
        try:
            # Lendo os dados da linha, tratando valores nulos para setor/cargo/unidade
            nome = row['NOME']
            data_nasc = row['Data de Nascimento']
            # Limpa e formata o CPF para garantir que tenha 11 dígitos
            cpf = str(row['CPF']).replace('.0', '')
            cpf = ''.join(filter(str.isdigit, cpf)).zfill(11)

            setor = row['SETOR'] if pd.notna(row['SETOR']) else None
            cargo = row['CARGO'] if pd.notna(row['CARGO']) else None
            unidade = row['UNIDADE'] if pd.notna(row['UNIDADE']) else None

            # SQL para inserir um novo colaborador ou atualizar um existente se o CPF já existir
            # A coluna 'ativo' será definida como 1 (TRUE) para todos os colaboradores na planilha
            sql_upsert = """
                INSERT INTO colaboradores (cpf, nome, data_nascimento, setor, cargo, unidade, ativo)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    nome = VALUES(nome),
                    data_nascimento = VALUES(data_nascimento),
                    setor = VALUES(setor),
                    cargo = VALUES(cargo),
                    unidade = VALUES(unidade),
                    ativo = 1;
            """
            cursor.execute(sql_upsert, (cpf, nome, data_nasc, setor, cargo, unidade))

        except Exception as e:
            print(f"❌ Erro ao processar a linha para o nome '{row.get('NOME', 'N/A')}': {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Importação e atualização de colaboradores concluída com sucesso.")


if __name__ == "__main__":
    main()