from datetime import datetime
from app import db
from sqlalchemy.dialects.sqlite import TEXT
from sqlalchemy import CheckConstraint

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 部门名称
    code = db.Column(db.String(20), nullable=True, unique=True)  # 部门编码，设置为可为空
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)  # 父部门ID
    description = db.Column(db.Text)  # 描述
    order = db.Column(db.Integer, default=0)  # 部门排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('Department', remote_side=[id], backref=db.backref('children', order_by=order))
    users = db.relationship('User', back_populates='department')
    
    def __repr__(self):
        return f'<Department {self.name}>' 