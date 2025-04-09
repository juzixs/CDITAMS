from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 初始化应用和数据库
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-cditams'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cditams.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# 注册蓝图
from app.views.auth import auth as auth_blueprint
from app.views.main import main as main_blueprint
from app.views.organization import organization as organization_blueprint

app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
app.register_blueprint(organization_blueprint)

if __name__ == '__main__':
    app.run(debug=True) 