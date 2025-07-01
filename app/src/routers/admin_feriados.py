from flask import Blueprint, render_template, request, flash, redirect, url_for
import csv
import io
# Importe a sua função de conexão central
from ..config.db import get_db_connection

admin_feriados_bp = Blueprint('admin_feriados', __name__, url_prefix='/admin')


@admin_feriados_bp.route('/feriados')
def gerenciar_feriados():
    return render_template('gerenciar_feriados/gerenciar_feriados.html')


@admin_feriados_bp.route('/feriados/upload', methods=['POST'])
def upload_feriados():
    file = request.files.get('csv_file')

    if not file or file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('admin_feriados.gerenciar_feriados'))

    if not file.filename.endswith('.csv'):
        flash('Formato de arquivo inválido. Por favor, envie um arquivo .csv.', 'danger')
        return redirect(url_for('admin_feriados.gerenciar_feriados'))

    # Agora a função get_db_connection() é a sua, vinda do arquivo central
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if request.form.get('delete_existing'):
            cursor.execute('DELETE FROM feriados')
            flash('Feriados existentes foram removidos.', 'info')

        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.reader(stream)
        next(csv_reader)

        insert_query = 'INSERT INTO feriados (data, descricao, unidade) VALUES (%s, %s, %s)'
        count = 0
        for row in csv_reader:
            if not all(row): continue

            cursor.execute(insert_query, (row[0], row[1].strip(), row[2].strip()))
            count += 1

        conn.commit()
        flash(f'{count} feriados importados com sucesso!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_feriados.gerenciar_feriados'))