from flask import Flask, render_template, Blueprint
from ..config.db import get_db_connection

app = Flask(__name__)

admin = Blueprint('admin', __name__, template_folder='views/admin')
@admin.route('/admin')
def admin_dashboard():
    # Renderizando o template 'admin.html' que está dentro da pasta views/admin
    return render_template('admin.html')

admin = Blueprint('login', __name__, template_folder='views/login')
@admin.route('/login')
def admin_dashboard():
    # Renderizando o template 'login.html' que está dentro da pasta views/login
    return render_template('login.html')

admin = Blueprint('login', __name__, template_folder='views/analitico')
@admin.route('/analitico')
def admin_dashboard():
    # Renderizando o template 'login.html' que está dentro da pasta views/analitico
    return render_template('analitico.html')

admin = Blueprint('login', __name__, template_folder='views/adminLogin')
@admin.route('/adminLogin')
def admin_dashboard():
    # Renderizando o template 'login.html' que está dentro da pasta views/admin-login
    return render_template('adminLogin.html')

