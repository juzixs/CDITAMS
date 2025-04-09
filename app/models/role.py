from datetime import datetime
import json
from app import db

# 角色-权限关联表
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # 角色名称
    identifier = db.Column(db.String(64), unique=True, nullable=False)  # 角色标识
    description = db.Column(db.String(255))  # 角色描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    users = db.relationship('User', back_populates='role')
    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))
    
    @staticmethod
    def insert_default_roles():
        # 创建默认的超级管理员角色
        if not Role.query.filter_by(identifier='super_admin').first():
            super_admin = Role(name='超级管理员', identifier='super_admin', 
                              description='系统超级管理员，拥有所有权限')
            
            # 添加所有权限给超级管理员
            all_permissions = Permission.query.all()
            for perm in all_permissions:
                super_admin.permissions.append(perm)
                
            db.session.add(super_admin)
            db.session.commit()
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 权限名称
    identifier = db.Column(db.String(64), unique=True, nullable=False)  # 权限标识
    module = db.Column(db.String(64))  # 所属模块
    parent_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=True)  # 父权限ID
    type = db.Column(db.String(20))  # 权限类型: 'page'(页面权限), 'button'(按钮权限)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    parent = db.relationship('Permission', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    
    @staticmethod
    def insert_default_permissions():
        # 创建基本权限结构
        permissions_data = [
            # 主页模块
            {'name': '首页', 'identifier': 'home', 'module': 'home', 'type': 'page'},
            
            # 组织模块
            {'name': '组织', 'identifier': 'organization', 'module': 'organization', 'type': 'page'},
            {'name': '用户管理', 'identifier': 'organization.users', 'module': 'organization', 'parent': 'organization', 'type': 'page'},
            {'name': '新增用户', 'identifier': 'organization.users.add', 'module': 'organization', 'parent': 'organization.users', 'type': 'button'},
            {'name': '编辑用户', 'identifier': 'organization.users.edit', 'module': 'organization', 'parent': 'organization.users', 'type': 'button'},
            {'name': '删除用户', 'identifier': 'organization.users.delete', 'module': 'organization', 'parent': 'organization.users', 'type': 'button'},
            {'name': '导入用户', 'identifier': 'organization.users.import', 'module': 'organization', 'parent': 'organization.users', 'type': 'button'},
            {'name': '导出用户', 'identifier': 'organization.users.export', 'module': 'organization', 'parent': 'organization.users', 'type': 'button'},
            
            {'name': '部门管理', 'identifier': 'organization.departments', 'module': 'organization', 'parent': 'organization', 'type': 'page'},
            {'name': '新增部门', 'identifier': 'organization.departments.add', 'module': 'organization', 'parent': 'organization.departments', 'type': 'button'},
            {'name': '编辑部门', 'identifier': 'organization.departments.edit', 'module': 'organization', 'parent': 'organization.departments', 'type': 'button'},
            {'name': '删除部门', 'identifier': 'organization.departments.delete', 'module': 'organization', 'parent': 'organization.departments', 'type': 'button'},
            
            {'name': '角色管理', 'identifier': 'organization.roles', 'module': 'organization', 'parent': 'organization', 'type': 'page'},
            {'name': '新增角色', 'identifier': 'organization.roles.add', 'module': 'organization', 'parent': 'organization.roles', 'type': 'button'},
            {'name': '编辑角色', 'identifier': 'organization.roles.edit', 'module': 'organization', 'parent': 'organization.roles', 'type': 'button'},
            {'name': '删除角色', 'identifier': 'organization.roles.delete', 'module': 'organization', 'parent': 'organization.roles', 'type': 'button'},
            
            # 其他模块权限...
        ]
        
        # 建立权限父子关系
        permission_map = {}
        
        # 第一轮：创建所有权限对象
        for perm_data in permissions_data:
            # 检查权限是否已存在
            identifier = perm_data['identifier']
            existing = Permission.query.filter_by(identifier=identifier).first()
            
            if not existing:
                new_permission = Permission(
                    name=perm_data['name'],
                    identifier=identifier,
                    module=perm_data['module'],
                    type=perm_data['type']
                )
                db.session.add(new_permission)
                permission_map[identifier] = new_permission
        
        db.session.commit()
        
        # 第二轮：设置父子关系
        for perm_data in permissions_data:
            if 'parent' in perm_data:
                child_identifier = perm_data['identifier']
                parent_identifier = perm_data['parent']
                
                child = permission_map.get(child_identifier) or Permission.query.filter_by(identifier=child_identifier).first()
                parent = permission_map.get(parent_identifier) or Permission.query.filter_by(identifier=parent_identifier).first()
                
                if child and parent:
                    child.parent_id = parent.id
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Permission {self.name}>' 