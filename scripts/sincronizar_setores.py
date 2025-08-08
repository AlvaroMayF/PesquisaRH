# app/scripts/sincronizar_setores.py (VERSÃO FINAL E DEFINITIVA)

import mysql.connector

# <<< CREDENCIAIS INSERIDAS DIRETAMENTE NO SCRIPT >>>
RH_CONFIG = {
    'host': '127.0.0.1',
    'user': 'pesquisa',
    'password': '1234',
    'database': 'pesquisa_rh',
    'auth_plugin': 'mysql_native_password'
}

IDSECURE_CONFIG = {
    'host': '10.0.1.0',
    'user': 'integracao',
    'password': '[]-@samar@hsp',
    'database': 'acesso',
    'port': 3306,
    'auth_plugin': 'mysql_native_password'
}


def sincronizar():
    """
    Lê todos os setores únicos do banco de dados do RH e os insere no banco
    de dados do iDSecure se eles ainda não existirem.
    """
    conn_rh = None
    conn_idsecure = None

    try:
        print("Conectando ao banco de dados do RH...")
        conn_rh = mysql.connector.connect(**RH_CONFIG)
        cur_rh = conn_rh.cursor(dictionary=True)
        print("✅ Conexão com o RH estabelecida.")

        print("\nConectando ao banco de dados do iDSecure...")
        conn_idsecure = mysql.connector.connect(**IDSECURE_CONFIG)
        cur_idsecure = conn_idsecure.cursor(dictionary=True)
        print("✅ Conexão com o iDSecure estabelecida.")

        print("\nBuscando setores no banco do RH...")
        cur_rh.execute("SELECT DISTINCT setor FROM colaboradores WHERE setor IS NOT NULL AND setor != ''")
        setores_rh = {row['setor'].strip().upper() for row in cur_rh.fetchall()}
        print(f"Encontrados {len(setores_rh)} setores únicos no RH.")

        print("Buscando grupos existentes no iDSecure...")
        cur_idsecure.execute("SELECT name FROM `groups`")
        grupos_idsecure = {row['name'].strip().upper() for row in cur_idsecure.fetchall()}
        print(f"Encontrados {len(grupos_idsecure)} grupos no iDSecure.")

        setores_a_inserir = setores_rh - grupos_idsecure
        if not setores_a_inserir:
            print("\nTodos os setores já estão sincronizados. Nenhuma ação necessária.")
            return

        print(f"\n{len(setores_a_inserir)} setores para sincronizar: {', '.join(setores_a_inserir)}")

        # <<< CORREÇÃO FINAL AQUI >>>
        # Adicionadas todas as colunas obrigatórias com seus valores padrão (0).
        print("Iniciando inserção...")
        sql_insert = """
            INSERT INTO `groups` (
                name, disableADE, controlVisitors, maxVisitors, contingency, idType
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        for setor in setores_a_inserir:
            try:
                # Agora passamos o nome do setor e os valores padrão 0 para os outros campos.
                cur_idsecure.execute(sql_insert, (setor, 0, 0, 0, 0, 0))
                print(f"  -> Setor '{setor}' inserido com sucesso.")
            except mysql.connector.Error as err:
                print(f"  -> ERRO ao inserir o setor '{setor}': {err}")

        conn_idsecure.commit()
        print("\n✅ Sincronização concluída com sucesso!")

    except mysql.connector.Error as err:
        print(f"\n❌ ERRO DE BANCO DE DADOS: {err}")
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
    finally:
        if conn_rh and conn_rh.is_connected():
            conn_rh.close()
        if conn_idsecure and conn_idsecure.is_connected():
            conn_idsecure.close()
        print("\nConexões fechadas.")


if __name__ == '__main__':
    sincronizar()