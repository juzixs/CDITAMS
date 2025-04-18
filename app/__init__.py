from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # 配置应用
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-for-cditams'
    
    # 获取项目根目录
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    # 设置数据库路径
    db_path = os.path.join(basedir, 'instance', 'cditams.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    
    # 注册蓝图
    from app.views.auth import auth
    from app.views.main import main
    from app.views.organization import organization
    from app.views.asset import asset
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(organization)
    app.register_blueprint(asset)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 导入models以确保创建所有表
        from app.models import User, Department, Role, Permission, Device, AssetCategory, AssetLocation, DeviceField
        
        # 插入默认权限和角色
        Permission.insert_default_permissions()
        Role.insert_default_roles()
        
        # 创建超级管理员账户（如果不存在）
        if not User.query.filter_by(employee_id='86000001').first():
            from app.models.user import User
            super_admin_role = Role.query.filter_by(identifier='super_admin').first()
            if super_admin_role:
                super_admin = User(
                    employee_id='86000001',
                    name='超级管理员',
                    gender='男',
                    role=super_admin_role
                )
                super_admin.password = 'password'
                db.session.add(super_admin)
                db.session.commit()
    
    return app 