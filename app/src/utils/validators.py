import re

def is_cpf_valid(cpf: str) -> bool:
    """
    Valida um CPF brasileiro. Retorna True se for válido, False caso contrário.
    """
    # 1. Garante que o CPF é uma string e remove a pontuação
    cpf = str(cpf).strip()
    cpf = re.sub(r'[^0-9]', '', cpf)

    # 2. Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False

    # 3. Verifica se todos os dígitos são iguais (ex: 111.111.111-11), que são inválidos
    if cpf == cpf[0] * 11:
        return False

    # 4. Cálculo do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    # 5. Cálculo do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False

    return True