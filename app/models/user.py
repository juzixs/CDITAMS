from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # 工号
    name = db.Column(db.String(64), nullable=False)  # 姓名
    gender = db.Column(db.String(10))  # 性别
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    is_active = db.Column(db.Boolean, default=True)  # 用户状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    department = db.relationship('Department', back_populates='users')
    role = db.relationship('Role', back_populates='users')
    
    @property
    def password(self):
        raise AttributeError('密码不是可读属性')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 