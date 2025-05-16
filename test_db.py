# test_db.py
from app.src.config.db import get_db_connection

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        # Para mysql-connector-python, você pode usar is_connected()
        alive = conn.is_connected()
        conn.close()
        if alive:
            print("👍 Conexão com o MySQL OK!")
        else:
            print("⚠️ Conexão aberta mas não está ativa.")
    except Exception as e:
        print("❌ Falha ao conectar ao MySQL:", e)
