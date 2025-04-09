from flask import Blueprint, render_template
from flask_login import login_required, current_user

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    return render_template('main/index.html', title='首页 - CDITAMS')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html', title='仪表盘 - CDITAMS') 