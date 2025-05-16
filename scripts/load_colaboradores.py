# scripts/load_colaboradores.py
import os
import pandas as pd
from mysql.connector import IntegrityError
from app.src.config.db import get_db_connection

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'colaboradores_samar.xlsx')

def main():
    # 1) Carrega a planilha
    df = pd.read_excel(EXCEL_PATH)

    # 2) Conecta ao banco
    conn = get_db_connection()
    cursor = conn.cursor()

    # 3) Loop e insert
    for _, row in df.iterrows():
        nome = row['Nome']
        data_nasc = row['Data de Nascimento']
        cpf = str(row['CPF'])
        try:
            cursor.execute(
                "INSERT INTO colaboradores (nome, data_nascimento, cpf) VALUES (%s, %s, %s)",
                (nome, data_nasc, cpf)
            )
        except IntegrityError:
            print(f"⚠️ Já existe colaborador com CPF {cpf}, pulando.")
        except Exception as e:
            print(f"❌ Erro ao inserir {cpf}:", e)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Importação concluída.")

if __name__ == "__main__":
    main()
