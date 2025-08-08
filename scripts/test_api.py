# Arquivo: test_api.py
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suprime apenas o aviso de requisição HTTPS não verificada
warnings.simplefilter('ignore', InsecureRequestWarning)

# --- Configure seus dados aqui ---
IDSECURE_BASE_URL = "https://10.0.1.0:30443"
IDSECURE_API_USER = "admin"
IDSECURE_API_PASSWORD = "admin123"
# ----------------------------------

login_url = f"{IDSECURE_BASE_URL}/api/login"
login_data = {
    "username": IDSECURE_API_USER,
    "password": IDSECURE_API_PASSWORD
}

print(f"Tentando fazer POST para: {login_url}")
print(f"Com os dados: {login_data}")

try:
    response = requests.post(
        login_url,
        json=login_data,  # Usando JSON, como no teste bem-sucedido do Postman
        timeout=15,
        verify=False      # Ignorando o certificado SSL
    )

    print("\n--- INÍCIO DA RESPOSTA DO SERVIDOR ---")
    print(f"Status Code: {response.status_code}")
    print("\nHeaders da Resposta:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")

    print("\nCorpo da Resposta (texto):")
    print(response.text)
    print("--- FIM DA RESPOSTA DO SERVIDOR ---\n")

    if response.status_code == 200:
        print("✅ SUCESSO: Login na API realizado com sucesso!")
    else:
        print(f"❌ FALHA: O servidor respondeu com o status {response.status_code}.")

except requests.exceptions.RequestException as e:
    print(f"\n❌ FALHA: Ocorreu um erro de conexão ao tentar acessar a API.")
    print(f"   Erro detalhado: {e}")