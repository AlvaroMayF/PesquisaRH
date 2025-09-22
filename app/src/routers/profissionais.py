# Arquivo: src/routers/profissionais.py

from flask import Blueprint, request, jsonify, current_app
from src.services import idsecure_db_service, rh_db_service
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import os
import time
import base64

# Cria o blueprint que será importado no run.py
profissionais_bp = Blueprint('profissionais', __name__)


# --- FUNÇÕES AUXILIARES PARA PROCESSAMENTO DE FOTO (copiadas do seu admin.py para consistência) ---

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_photo(request_obj):
    """Processa a foto vinda do formulário (upload ou webcam) e a salva localmente."""
    base_path = current_app.config.get('FOTOS_FOLDER')
    if not base_path:
        return None, "ERRO DE CONFIGURAÇÃO: 'FOTOS_FOLDER' não foi definida."

    timestamp = int(time.time())

    # Tenta pegar a foto de um upload de arquivo
    foto_upload = request_obj.files.get('foto')
    if foto_upload and foto_upload.filename != '' and allowed_file(foto_upload.filename):
        try:
            img = Image.open(foto_upload.stream).convert('RGB')
            base_filename = os.path.splitext(secure_filename(foto_upload.filename))[0]
            foto_filename = f"{timestamp}_{base_filename}.jpg"
            save_path = os.path.join(base_path, foto_filename)
            img.save(save_path, 'jpeg', quality=90)
            return foto_filename, None
        except Exception as e:
            return None, f"ERRO AO PROCESSAR IMAGEM ANEXADA: {e}"

    # Se não houver upload, tenta pegar da webcam (base64)
    foto_base64 = request_obj.form.get('foto_base64')
    if foto_base64 and ',' in foto_base64:
        try:
            img_data_str = foto_base64.split(',')[1]
            img_data = base64.b64decode(img_data_str)
            img = Image.open(BytesIO(img_data)).convert('RGB')
            foto_filename = f"webcam_{timestamp}.jpg"
            save_path = os.path.join(base_path, foto_filename)
            img.save(save_path, 'jpeg', quality=90)
            return foto_filename, None
        except Exception as e:
            return None, f"ERRO AO PROCESSAR IMAGEM DA WEBCAM: {e}"

    return None, None


@profissionais_bp.route('/api/enfermagem/add', methods=['POST'])
def add_enfermagem():
    try:
        # MUDANÇA 1: Processar a foto primeiro
        foto_filename, error_msg = process_photo(request)
        if error_msg:
            return jsonify({"success": False, "message": error_msg}), 500

        # MUDANÇA 2: Ler dados de request.form em vez de request.get_json()
        rh_data = {
            "nome": request.form.get('nome'),
            "cpf": request.form.get('cpf'),
            "data_nascimento": request.form.get('data_nascimento'),
            "coren": request.form.get('coren'),
            "cargo": request.form.get('cargo'),
            "setor": request.form.get('setor'),
            "unidade": request.form.get('unidade'),
            "data_admissao": request.form.get('data_admissao'),
            "tipo_cadastro": "ENFERMAGEM",
            "foto_filename": foto_filename  # Adiciona o nome do arquivo da foto
        }

        # Validação básica de campos obrigatórios
        if not all([rh_data['nome'], rh_data['cpf'], rh_data['coren'], rh_data['cargo'], rh_data['setor']]):
            return jsonify({"success": False, "message": "Campos obrigatórios não preenchidos."}), 400

        # Inserir no banco do RH primeiro
        rh_id, rh_error = rh_db_service.create_colaborador(rh_data)
        if rh_error:
            return jsonify({"success": False, "message": f"Erro ao salvar no RH: {rh_error}"}), 500

        # Inserir no banco iDSecure
        idsecure_id, idsecure_error = idsecure_db_service.create_idsecure_user(
            nome=rh_data['nome'],
            cpf=rh_data['cpf'],
            pis=None,
            senha=rh_data['data_nascimento'],
            matricula=rh_id,
            setor=rh_data['setor']
        )

        if idsecure_error:
            return jsonify({"success": False,
                            "message": f"Usuário criado no RH (ID: {rh_id}), mas falhou ao criar no iDSecure: {idsecure_error}"}), 500

        # Se houver foto, envia para o iDSecure
        if foto_filename:
            photo_success, photo_error = idsecure_db_service.add_photo_to_idsecure(idsecure_id, foto_filename)
            if not photo_success:
                return jsonify({"success": False, "message": f"Usuário criado, mas FALHA na foto: {photo_error}"})

        # Aciona a sincronização final
        idsecure_db_service.trigger_idsecure_sync(idsecure_id)

        return jsonify({
            "success": True,
            "message": "Profissional de enfermagem cadastrado e sincronizado com sucesso!"
        }), 201

    except Exception as e:
        print(f"ERRO CRÍTICO NA ROTA add_enfermagem: {e}")
        return jsonify({"success": False, "message": f"Ocorreu um erro inesperado no servidor: {e}"}), 500


@profissionais_bp.route('/api/medico/add', methods=['POST'])
def add_medico():
    try:
        # MUDANÇA 1: Processar a foto primeiro
        foto_filename, error_msg = process_photo(request)
        if error_msg:
            return jsonify({"success": False, "message": error_msg}), 500

        # MUDANÇA 2: Ler dados de request.form
        rh_data = {
            "nome": request.form.get('nome'),
            "cpf": request.form.get('cpf'),
            "data_nascimento": request.form.get('data_nascimento'),
            "crm": request.form.get('crm'),
            "especialidade": request.form.get('especialidade'),
            "cargo": request.form.get('cargo'),
            "setor": request.form.get('setor'),
            "unidade": request.form.get('unidade'),
            "data_admissao": request.form.get('data_admissao'),  # Corrigido de 'data_contrato' para 'data_admissao'
            "tipo_cadastro": "MEDICO",
            "foto_filename": foto_filename
        }

        # Validação básica
        if not all([rh_data['nome'], rh_data['cpf'], rh_data['crm'], rh_data['especialidade']]):
            return jsonify({"success": False, "message": "Campos obrigatórios para médico não preenchidos."}), 400

        # Inserir no banco do RH
        rh_id, rh_error = rh_db_service.create_colaborador(rh_data)
        if rh_error:
            return jsonify({"success": False, "message": f"Erro ao salvar no RH: {rh_error}"}), 500

        # Inserir no iDSecure
        idsecure_id, idsecure_error = idsecure_db_service.create_idsecure_user(
            nome=rh_data['nome'],
            cpf=rh_data['cpf'],
            pis=None,
            senha=rh_data['data_nascimento'],
            matricula=rh_id,
            setor=rh_data['setor']
        )

        if idsecure_error:
            return jsonify({"success": False,
                            "message": f"Usuário criado no RH (ID: {rh_id}), mas falhou ao criar no iDSecure: {idsecure_error}"}), 500

        # Se houver foto, envia para o iDSecure
        if foto_filename:
            photo_success, photo_error = idsecure_db_service.add_photo_to_idsecure(idsecure_id, foto_filename)
            if not photo_success:
                return jsonify({"success": False, "message": f"Usuário criado, mas FALHA na foto: {photo_error}"})

        # Aciona a sincronização final
        idsecure_db_service.trigger_idsecure_sync(idsecure_id)

        return jsonify({
            "success": True,
            "message": "Médico cadastrado e sincronizado com sucesso!"
        }), 201

    except Exception as e:
        print(f"ERRO CRÍTICO NA ROTA add_medico: {e}")
        return jsonify({"success": False, "message": f"Ocorreu um erro inesperado no servidor: {e}"}), 500