# gerar_senha.py
from werkzeug.security import generate_password_hash

# Coloque a senha que você quer criptografar aqui
senha_admin = "S@m@ar2025#"
senha_recepcao = "hspsamar@2025"

# Gera as versões criptografadas
hash_admin = generate_password_hash(senha_admin)
hash_recepcao = generate_password_hash(senha_recepcao)

print("--- COPIE E COLE OS VALORES ABAIXO NO BANCO DE DADOS ---")
print(f"Hash para 'admin': {hash_admin}")
print(f"Hash para 'recepcao': {hash_recepcao}")