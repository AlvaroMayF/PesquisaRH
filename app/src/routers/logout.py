from flask import Blueprint, session, redirect, url_for, flash

# Blueprint para logout de usuários
logout_bp = Blueprint('logout', __name__) # Renomeei para logout_bp para consistência

@logout_bp.route('/logout')
def logout_view():
    """
    Finaliza a sessão do usuário e redireciona para a página de login.
    """
    session.clear() # Limpa todos os dados da sessão

    # Adiciona uma mensagem para o usuário saber que saiu com sucesso
    flash('Você saiu do sistema com segurança.', 'success') 

    # CORREÇÃO: Redireciona para a página de login.
    return redirect(url_for('auth.login'))