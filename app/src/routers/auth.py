from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# Importa a sua função de conexão com o banco de dados
from ..config.db import get_db_connection

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='../views'
)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        data_nascimento = request.form.get('data_nascimento')

        # Validação para garantir que os campos não estão vazios
        if not cpf or not data_nascimento:
            # SINTAXE CORRIGIDA: A categoria 'error' é o segundo argumento.
            flash('Por favor, preencha todos os campos.', 'error')
            return redirect(url_for('auth.login'))

        # Limpa o CPF para buscar no banco (remove pontos e traço)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))

        colaborador = None
        conn = None  # Inicia a conexão como nula
        try:
            # --- INÍCIO DA LÓGICA DE BANCO DE DADOS REAL ---
            conn = get_db_connection()
            if conn:
                # dictionary=True faz o cursor retornar os resultados como dicionários
                cursor = conn.cursor(dictionary=True)  # CORRIGIDO: sem duplicar 'conn'

                query = "SELECT id, nome FROM colaboradores WHERE cpf = %s AND data_nascimento = %s"
                cursor.execute(query, (cpf_limpo, data_nascimento))
                colaborador = cursor.fetchone()

                cursor.close()
            else:
                flash("Não foi possível conectar ao banco de dados.", "error")
                return redirect(url_for('auth.login'))
            # --- FIM DA LÓGICA DE BANCO DE DADOS REAL ---

        except Exception as e:
            # Em caso de erro, informa no console e mostra uma mensagem genérica
            print(f"❌ Erro na consulta ao banco de dados: {e}")
            flash("Ocorreu um erro ao tentar validar o acesso. Tente novamente.", "error")
            return redirect(url_for('auth.login'))
        finally:
            # Garante que a conexão com o banco seja sempre fechada
            if conn:
                conn.close()

        if colaborador:
            # Login bem-sucedido!
            session.clear()
            session['colaborador_id'] = colaborador['id']
            session['colaborador_nome'] = colaborador['nome']

            # Redireciona para a página principal após o login
            return redirect(url_for('home.home_view'))
        else:
            # Login falhou
            flash('CPF e/ou Data de Nascimento não encontrados ou incorretos.', 'error')
            return redirect(url_for('auth.login'))

    # Se o método for GET, apenas exibe a página de login
    return render_template('Login/login.html')