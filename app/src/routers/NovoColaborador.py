from flask import Blueprint, render_template, request, redirect, url_for

novo_colaborador_bp = Blueprint('novo_colaborador', __name__)

@novo_colaborador_bp.route('/admin/novo-colaborador', methods=['GET', 'POST'])
def novo_colaborador():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        data_nascimento = request.form['data_nascimento']
        print(f"Novo colaborador: {nome}, {cpf}, {data_nascimento}")
        return redirect(url_for('novo_colaborador.novo_colaborador'))
    return render_template('NovoColaborador/NovoColaborador.html')
