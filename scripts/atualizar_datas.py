import pandas as pd
import os

# ==============================================================================
# ÁREA DE CONFIGURAÇÃO - AJUSTADO PARA A ESTRUTURA EXATA DOS SEUS ARQUIVOS
# ==============================================================================
# Arquivos (devem estar na pasta 'data')
ARQUIVO_PRINCIPAL_NOME = 'colaboradores_samar.xlsx'
ARQUIVO_COM_DATAS_NOME = 'addm.xlsx'
ARQUIVO_FINAL_NOME = 'colaboradores_samar.xlsx'

# Nomes das colunas (baseado nos seus prints)
# Arquivo principal (colaboradores_samar.xlsx)
COLUNA_CPF_PRINCIPAL = 'CPF'
COLUNA_ADMISSAO_PRINCIPAL = 'Admissão'  # A coluna que será preenchida

# Arquivo com as datas (addm.xlsx)
COLUNA_CPF_DATAS = 'CPF'
COLUNA_ADMISSAO_DATAS = 'Admissão'


# ==============================================================================
# O SCRIPT COMEÇA AQUI - NÃO PRECISA MODIFICAR NADA ABAIXO
# ==============================================================================

def get_full_path(folder_name, file_name):
    """Constrói o caminho completo para um arquivo a partir da raiz do projeto."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, folder_name, file_name)


def limpar_cpf(cpf):
    """Função para limpar e padronizar o CPF, removendo pontuação."""
    if pd.isna(cpf):
        return None
    return str(cpf).strip().replace('.', '').replace('-', '')


def atualizar_planilha():
    print("Iniciando o script de atualização de datas de admissão...")

    arquivo_principal_path = get_full_path('data', ARQUIVO_PRINCIPAL_NOME)
    arquivo_datas_path = get_full_path('data', ARQUIVO_COM_DATAS_NOME)
    arquivo_final_path = get_full_path('data', ARQUIVO_FINAL_NOME)

    if not os.path.exists(arquivo_principal_path) or not os.path.exists(arquivo_datas_path):
        print(
            f"\nERRO: Verifique se os arquivos '{ARQUIVO_PRINCIPAL_NOME}' e '{ARQUIVO_COM_DATAS_NOME}' existem na pasta 'data'.")
        return

    try:
        print(f"Lendo arquivo principal: '{ARQUIVO_PRINCIPAL_NOME}'...")
        # Lê o arquivo principal, garantindo que o CPF seja tratado como texto
        df_principal = pd.read_excel(arquivo_principal_path, dtype={COLUNA_CPF_PRINCIPAL: str})

        print(f"Lendo arquivo com as datas: '{ARQUIVO_COM_DATAS_NOME}'...")
        # Lê o arquivo com as datas, garantindo que o CPF seja tratado como texto
        df_datas = pd.read_excel(arquivo_datas_path, dtype={COLUNA_CPF_DATAS: str})

        print("\nArquivos lidos. Criando mapa de CPF para Data de Admissão...")

        # Limpa os CPFs do arquivo de DATAS para criar o mapa
        df_datas['cpf_limpo'] = df_datas[COLUNA_CPF_DATAS].apply(limpar_cpf)
        df_datas.dropna(subset=['cpf_limpo'], inplace=True)

        # Cria o dicionário (mapa) que liga cada CPF à sua data de admissão.
        # drop_duplicates garante que, se houver CPFs repetidos, pegamos apenas a primeira data.
        mapa_de_datas = df_datas.drop_duplicates(subset=['cpf_limpo']).set_index('cpf_limpo')[COLUNA_ADMISSAO_DATAS]

        print("Mapa criado. Preenchendo a coluna de admissão no arquivo principal...")

        # Limpa os CPFs do arquivo PRINCIPAL para fazer a busca no mapa
        df_principal['cpf_limpo'] = df_principal[COLUNA_CPF_PRINCIPAL].apply(limpar_cpf)

        # Preenche a coluna 'Admissão' usando o mapa.
        # A função .map() faz o "PROCV" de forma eficiente.
        # Apenas as linhas com CPF correspondente no mapa serão preenchidas.
        df_principal[COLUNA_ADMISSAO_PRINCIPAL] = df_principal['cpf_limpo'].map(mapa_de_datas)

        # Remove a coluna temporária de CPF limpo, ela não é mais necessária.
        df_principal.drop(columns=['cpf_limpo'], inplace=True)

        # Formata a coluna para garantir que fique apenas a data (sem horas)
        df_principal[COLUNA_ADMISSAO_PRINCIPAL] = pd.to_datetime(df_principal[COLUNA_ADMISSAO_PRINCIPAL],
                                                                 errors='coerce').dt.date

        total_linhas = len(df_principal)
        datas_preenchidas = df_principal[COLUNA_ADMISSAO_PRINCIPAL].notna().sum()

        print("\n--- Relatório da Atualização ---")
        print(f"Total de colaboradores no arquivo: {total_linhas}")
        print(f"Total de colaboradores com data de admissão preenchida: {datas_preenchidas}")
        print("----------------------------------\n")

        print(f"Salvando o resultado em '{arquivo_final_path}'...")
        # Salva o DataFrame completo, com todas as colunas originais preservadas.
        df_principal.to_excel(arquivo_final_path, index=False)

        print("\nProcesso concluído com sucesso!")
        print(
            f"O arquivo '{ARQUIVO_FINAL_NOME}' foi gerado na pasta 'data' com todas as colunas e as datas atualizadas.")

    except KeyError as e:
        print(f"\nERRO: Coluna não encontrada: {e}.")
        print(
            "Verifique se os nomes das colunas na 'ÁREA DE CONFIGURAÇÃO' do script estão exatamente iguais aos das planilhas.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")


if __name__ == "__main__":
    atualizar_planilha()