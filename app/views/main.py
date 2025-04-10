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

# 资产模块路由重定向
@main.route('/assets')
@login_required
def assets():
    return render_template('asset/index.html') 