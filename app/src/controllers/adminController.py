from flask import Flask, render_template, Blueprint
from ..config.db import get_db_connection

app = Flask(__name__)

admin = Blueprint('admin', __name__, template_folder='views/admin')
@admin.route('/admin')
def admin_dashboard():
    # Renderizando o template 'admin.html' que está dentro da pasta views/admin
    return render_template('admin.html')

admin = Blueprint('home', __name__, template_folder='views/home')
@admin.route('/home')
def admin_dashboard():
    # Renderizando o template 'home.html' que está dentro da pasta views/home
    return render_template('home.html')

admin = Blueprint('home', __name__, template_folder='views/analitico')
@admin.route('/analitico')
def admin_dashboard():
    # Renderizando o template 'home.html' que está dentro da pasta views/analitico
    return render_template('analitico.html')

admin = Blueprint('home', __name__, template_folder='views/adminLogin')
@admin.route('/adminLogin')
def admin_dashboard():
    # Renderizando o template 'home.html' que está dentro da pasta views/admin-home
    return render_template('adminLogin.html')

