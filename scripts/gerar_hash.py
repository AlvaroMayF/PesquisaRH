from werkzeug.security import generate_password_hash

# A senha que você quer criptografar
senha_para_hash = "hspsamar@2025"

# O método exato que seu banco de dados usa (visto na imagem)
metodo_scrypt = 'scrypt:32768:8:1'

# Gerando o hash
hash_final = generate_password_hash(senha_para_hash, method=metodo_scrypt)

print("--- HASH GERADO ---")
print("Copie o valor abaixo e use no seu comando SQL.")
print("\n" + hash_final + "\n")