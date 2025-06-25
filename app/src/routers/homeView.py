from flask import Blueprint, render_template

home = Blueprint('home', __name__, url_prefix='')

@home.route('/', methods=['GET'])
def home_view():
    """Renderiza só o painel RH."""
    return render_template('home/home.html')
