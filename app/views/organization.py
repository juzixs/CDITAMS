from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.department import Department
from app.models.role import Role, Permission
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
import json

organization = Blueprint('organization', __name__, url_prefix='/organization')

# 用户表单
class UserForm(FlaskForm):
    employee_id = StringField('工号', validators=[DataRequired(), Length(1, 20)])
    name = StringField('姓名', validators=[DataRequired(), Length(1, 64)])
    gender = SelectField('性别', choices=[('男', '男'), ('女', '女')])
    password = PasswordField('密码')
    email = StringField('邮箱', validators=[Optional(), Email()])
    phone = StringField('电话', validators=[Optional(), Length(1, 20)])
    department_id = SelectField('部门', coerce=int)
    role_id = SelectField('角色', coerce=int)
    is_active = BooleanField('启用账户', default=True)
    submit = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]
        self.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]

# 部门表单
class DepartmentForm(FlaskForm):
    name = StringField('部门名称', validators=[DataRequired(), Length(1, 64)])
    code = StringField('部门编码', validators=[Optional(), Length(1, 20)])
    parent_id = SelectField('上级部门', coerce=int, validators=[Optional()])
    description = TextAreaField('描述')
    submit = SubmitField('提交')
    
    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
        self.parent_id.choices = [(0, '无')] + [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]

# 角色表单
class RoleForm(FlaskForm):
    name = StringField('角色名称', validators=[DataRequired(), Length(1, 64)])
    identifier = StringField('角色标识', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField('描述')
    submit = SubmitField('提交')

# 用户管理路由
@organization.route('/users')
@login_required
def users():
    # 搜索和筛选
    search = request.args.get('search', '')
    department_id = request.args.get('department_id', type=int)
    role_id = request.args.get('role_id', type=int)
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.name.contains(search)) | 
            (User.employee_id.contains(search))
        )
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    if role_id:
        query = query.filter_by(role_id=role_id)
    
    # 分页
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(User.id).paginate(page=page, per_page=10, error_out=False)
    users = pagination.items
    
    # 获取部门和角色列表，用于筛选
    departments = Department.query.all()
    roles = Role.query.all()
    
    return render_template('organization/users.html', 
                          users=users,
                          pagination=pagination,
                          departments=departments,
                          roles=roles,
                          search=search,
                          department_id=department_id,
                          role_id=role_id,
                          title='用户管理 - CDITAMS')

@organization.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            employee_id=form.employee_id.data,
            name=form.name.data,
            gender=form.gender.data,
            email=form.email.data,
            phone=form.phone.data,
            department_id=form.department_id.data if form.department_id.data else None,
            role_id=form.role_id.data if form.role_id.data else None,
            is_active=form.is_active.data
        )
        
        if form.password.data:
            user.password = form.password.data
        
        db.session.add(user)
        try:
            db.session.commit()
            flash('用户添加成功。', 'success')
            return redirect(url_for('organization.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加用户失败: {str(e)}', 'danger')
    
    return render_template('organization/user_form.html', form=form, title='添加用户 - CDITAMS')

@organization.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.employee_id = form.employee_id.data
        user.name = form.name.data
        user.gender = form.gender.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.department_id = form.department_id.data if form.department_id.data else None
        user.role_id = form.role_id.data if form.role_id.data else None
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.password = form.password.data
        
        try:
            db.session.commit()
            flash('用户信息更新成功。', 'success')
            return redirect(url_for('organization.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新用户失败: {str(e)}', 'danger')
    
    return render_template('organization/user_form.html', form=form, user=user, title='编辑用户 - CDITAMS')

@organization.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash('用户删除成功。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除用户失败: {str(e)}', 'danger')
    
    return redirect(url_for('organization.users'))

@organization.route('/users/permissions/<int:id>')
@login_required
def user_permissions(id):
    user = User.query.get_or_404(id)
    permissions = []
    
    if user.role:
        role_permissions = user.role.permissions
        permissions = [p.id for p in role_permissions]
    
    # 获取所有权限的树状结构
    all_permissions = Permission.query.filter_by(parent_id=None).all()
    permission_tree = []
    
    for p in all_permissions:
        permission_tree.append(build_permission_tree(p, permissions))
    
    return render_template('organization/user_permissions.html', 
                          user=user, 
                          permission_tree=permission_tree,
                          title=f'{user.name} 权限 - CDITAMS')

# 部门管理路由
@organization.route('/departments')
@login_required
def departments():
    try:
        departments = Department.query.all()
        return render_template('organization/departments.html', 
                             departments=departments,
                             title='部门管理 - CDITAMS')
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print("Error in departments view:", str(e))
        print("Traceback:", error_traceback)
        flash(f'加载部门页面出错: {str(e)}', 'danger')
        return render_template('main/index.html', title='首页 - CDITAMS')

@organization.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        department = Department(
            name=form.name.data,
            code=form.code.data,
            parent_id=parent_id,
            description=form.description.data
        )
        
        db.session.add(department)
        try:
            db.session.commit()
            flash('部门添加成功。', 'success')
            return redirect(url_for('organization.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加部门失败: {str(e)}', 'danger')
    
    return render_template('organization/department_form.html', form=form, title='添加部门 - CDITAMS')

@organization.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    
    if department.parent_id:
        form.parent_id.data = department.parent_id
    else:
        form.parent_id.data = 0
    
    if form.validate_on_submit():
        department.name = form.name.data
        department.code = form.code.data
        department.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        department.description = form.description.data
        
        try:
            db.session.commit()
            flash('部门信息更新成功。', 'success')
            return redirect(url_for('organization.departments'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新部门失败: {str(e)}', 'danger')
    
    return render_template('organization/department_form.html', form=form, department=department, title='编辑部门 - CDITAMS')

@organization.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    
    # 检查是否有子部门
    if Department.query.filter_by(parent_id=id).first():
        flash('无法删除有子部门的部门。', 'danger')
        return redirect(url_for('organization.departments'))
    
    # 检查是否有用户
    if User.query.filter_by(department_id=id).first():
        flash('无法删除有用户的部门。', 'danger')
        return redirect(url_for('organization.departments'))
    
    try:
        db.session.delete(department)
        db.session.commit()
        flash('部门删除成功。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除部门失败: {str(e)}', 'danger')
    
    return redirect(url_for('organization.departments'))

@organization.route('/departments/update_order', methods=['POST'])
@login_required
def update_department_order():
    data = request.json
    try:
        for item in data:
            dept_id = item['id']
            order = item['order']
            parent_id = item.get('parent_id')
            
            dept = Department.query.get(dept_id)
            if dept:
                dept.order = order
                dept.parent_id = parent_id
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# 角色管理路由
@organization.route('/roles')
@login_required
def roles():
    roles = Role.query.all()
    return render_template('organization/roles.html', roles=roles, title='角色管理 - CDITAMS')

@organization.route('/roles/add', methods=['GET', 'POST'])
@login_required
def add_role():
    form = RoleForm()
    all_permissions = Permission.query.filter_by(parent_id=None).all()
    permission_tree = []
    
    for p in all_permissions:
        permission_tree.append(build_permission_tree(p, []))
    
    if form.validate_on_submit():
        role = Role(
            name=form.name.data,
            identifier=form.identifier.data,
            description=form.description.data
        )
        
        # 处理权限
        permission_ids = request.form.getlist('permissions')
        for pid in permission_ids:
            permission = Permission.query.get(int(pid))
            if permission:
                role.permissions.append(permission)
        
        db.session.add(role)
        try:
            db.session.commit()
            flash('角色添加成功。', 'success')
            return redirect(url_for('organization.roles'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加角色失败: {str(e)}', 'danger')
    
    return render_template('organization/role_form.html', 
                          form=form, 
                          permission_tree=permission_tree,
                          title='添加角色 - CDITAMS')

@organization.route('/roles/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_role(id):
    role = Role.query.get_or_404(id)
    form = RoleForm(obj=role)
    
    # 获取当前角色的权限
    role_permissions = [p.id for p in role.permissions]
    
    # 获取权限树
    all_permissions = Permission.query.filter_by(parent_id=None).all()
    permission_tree = []
    
    for p in all_permissions:
        permission_tree.append(build_permission_tree(p, role_permissions))
    
    if form.validate_on_submit():
        role.name = form.name.data
        role.identifier = form.identifier.data
        role.description = form.description.data
        
        # 更新权限
        role.permissions = []
        permission_ids = request.form.getlist('permissions')
        for pid in permission_ids:
            permission = Permission.query.get(int(pid))
            if permission:
                role.permissions.append(permission)
        
        try:
            db.session.commit()
            flash('角色信息更新成功。', 'success')
            return redirect(url_for('organization.roles'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新角色失败: {str(e)}', 'danger')
    
    return render_template('organization/role_form.html', 
                          form=form, 
                          role=role,
                          permission_tree=permission_tree,
                          title='编辑角色 - CDITAMS')

@organization.route('/roles/delete/<int:id>', methods=['POST'])
@login_required
def delete_role(id):
    role = Role.query.get_or_404(id)
    
    # 检查是否有用户使用此角色
    if User.query.filter_by(role_id=id).first():
        flash('无法删除被用户使用的角色。', 'danger')
        return redirect(url_for('organization.roles'))
    
    try:
        db.session.delete(role)
        db.session.commit()
        flash('角色删除成功。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除角色失败: {str(e)}', 'danger')
    
    return redirect(url_for('organization.roles'))

# 辅助函数
def build_permission_tree(permission, selected_permissions):
    """递归构建权限树"""
    node = {
        'id': permission.id,
        'name': permission.name,
        'identifier': permission.identifier,
        'type': permission.type,
        'checked': permission.id in selected_permissions,
        'children': []
    }
    
    children = permission.children.all()
    if children:
        for child in children:
            node['children'].append(build_permission_tree(child, selected_permissions))
    
    return node

def build_department_tree(departments, parent_id=None):
    """递归构建部门树"""
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            node = {
                'id': dept.id,
                'name': dept.name,
                'code': dept.code,
                'order': dept.order,
                'children': build_department_tree(departments, dept.id)
            }
            tree.append(node)
    return tree 