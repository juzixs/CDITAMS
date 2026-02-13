from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from .models import User, Department, Role, Permission, LoginLog
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


def user_login(request):
    if request.method == 'POST':
        emp_no = request.POST.get('emp_no', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember', False)
        
        user = authenticate(request, username=emp_no, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                LoginLog.objects.create(
                    user=user,
                    username=emp_no,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    action='login',
                    message='登录成功'
                )
                next_url = request.GET.get('next', '/')
                return HttpResponseRedirect(next_url)
            else:
                messages.error(request, '账户已被禁用')
        else:
            LoginLog.objects.create(
                username=emp_no,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                action='login_fail',
                message='登录失败：用户名或密码错误'
            )
            messages.error(request, '工号或密码错误')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    if request.user.is_authenticated:
        LoginLog.objects.create(
            user=request.user,
            username=request.user.emp_no,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            action='logout',
            message='退出登录'
        )
    logout(request)
    return redirect('login')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def index(request):
    return redirect('dashboard')


@login_required
def dashboard(request):
    from apps.assets.models import Device
    from apps.inventory.models import InventoryPlan, InventoryTask
    from apps.todos.models import Todo
    
    stats = {
        'total_devices': Device.objects.count(),
        'normal_devices': Device.objects.filter(status='normal').count(),
        'fault_devices': Device.objects.filter(status='fault').count(),
        'scrapped_devices': Device.objects.filter(status='scrapped').count(),
        'total_plans': InventoryPlan.objects.count(),
        'pending_tasks': InventoryTask.objects.filter(status='pending').count(),
        'my_todos': Todo.objects.filter(assignee=request.user, status='pending').count(),
    }
    
    return render(request, 'accounts/dashboard.html', {'stats': stats})


@login_required
def user_list(request):
    search = request.GET.get('search', '')
    dept_id = request.GET.get('department', '')
    role_id = request.GET.get('role', '')
    
    users = User.objects.select_related('department', 'role').all()
    
    if search:
        users = users.filter(Q(emp_no__icontains=search) | Q(realname__icontains=search) | Q(phone__icontains=search))
    if dept_id:
        users = users.filter(department_id=dept_id)
    if role_id:
        users = users.filter(role_id=role_id)
    
    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    departments = Department.objects.all()
    roles = Role.objects.all()
    
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'departments': departments,
        'roles': roles,
    })


@login_required
def user_create(request):
    if request.method == 'POST':
        emp_no = request.POST.get('emp_no')
        realname = request.POST.get('realname')
        password = request.POST.get('password', 'password')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        gender = request.POST.get('gender')
        department_id = request.POST.get('department')
        role_id = request.POST.get('role')
        
        if User.objects.filter(emp_no=emp_no).exists():
            messages.error(request, '工号已存在')
        else:
            user = User.objects.create_user(
                username=emp_no,
                emp_no=emp_no,
                realname=realname,
                password=password,
                email=email,
                phone=phone,
                gender=gender,
                department_id=department_id if department_id else None,
                role_id=role_id if role_id else None,
            )
            messages.success(request, '用户创建成功')
            return redirect('user_list')
    
    departments = Department.objects.all()
    roles = Role.objects.all()
    return render(request, 'accounts/user_form.html', {'departments': departments, 'roles': roles})


@login_required
def user_edit(request, pk):
    user = User.objects.get(pk=pk)
    
    if request.method == 'POST':
        user.realname = request.POST.get('realname')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.gender = request.POST.get('gender')
        user.department_id = request.POST.get('department') or None
        user.role_id = request.POST.get('role') or None
        user.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, '用户更新成功')
        return redirect('user_list')
    
    departments = Department.objects.all()
    roles = Role.objects.all()
    return render(request, 'accounts/user_form.html', {'user': user, 'departments': departments, 'roles': roles})


@login_required
def user_delete(request, pk):
    if request.method == 'POST':
        user = User.objects.get(pk=pk)
        if user.is_superuser:
            messages.error(request, '不能删除超级管理员')
        else:
            user.delete()
            messages.success(request, '用户删除成功')
    return redirect('user_list')


@login_required
def user_detail(request, pk):
    user = User.objects.select_related('department', 'role').get(pk=pk)
    return render(request, 'accounts/user_detail.html', {'user': user})


@login_required
def user_reset_password(request, pk):
    user = User.objects.get(pk=pk)
    if request.method == 'POST':
        password = request.POST.get('password', 'password')
        user.set_password(password)
        user.save()
        messages.success(request, f'密码已重置为: {password}')
        return redirect('user_list')
    return render(request, 'accounts/user_reset_password.html', {'user': user})


@login_required
def department_list(request):
    departments = Department.objects.filter(parent__isnull=True).prefetch_related('children')
    return render(request, 'accounts/department_list.html', {'departments': departments})


@login_required
def department_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        parent_id = request.POST.get('parent')
        description = request.POST.get('description')
        sort = request.POST.get('sort', 0)
        
        if Department.objects.filter(code=code).exists():
            messages.error(request, '部门编码已存在')
        else:
            Department.objects.create(
                name=name,
                code=code,
                parent_id=parent_id if parent_id else None,
                description=description,
                sort=sort
            )
            messages.success(request, '部门创建成功')
            return redirect('department_list')
    
    departments = Department.objects.all()
    return render(request, 'accounts/department_form.html', {'departments': departments})


@login_required
def department_edit(request, pk):
    dept = Department.objects.get(pk=pk)
    
    if request.method == 'POST':
        dept.name = request.POST.get('name')
        dept.code = request.POST.get('code')
        dept.parent_id = request.POST.get('parent') or None
        dept.description = request.POST.get('description')
        dept.sort = request.POST.get('sort', 0)
        dept.save()
        messages.success(request, '部门更新成功')
        return redirect('department_list')
    
    departments = Department.objects.exclude(pk=pk)
    return render(request, 'accounts/department_form.html', {'department': dept, 'departments': departments})


@login_required
def department_delete(request, pk):
    if request.method == 'POST':
        dept = Department.objects.get(pk=pk)
        if dept.children.exists() or dept.users.exists():
            messages.error(request, '该部门下有子部门或用户，无法删除')
        else:
            dept.delete()
            messages.success(request, '部门删除成功')
    return redirect('department_list')


@login_required
def role_list(request):
    roles = Role.objects.prefetch_related('permissions').all()
    return render(request, 'accounts/role_list.html', {'roles': roles})


@login_required
def role_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description')
        sort = request.POST.get('sort', 0)
        permission_ids = request.POST.getlist('permissions')
        
        role = Role.objects.create(
            name=name,
            code=code,
            description=description,
            sort=sort
        )
        if permission_ids:
            role.permissions.set(permission_ids)
        messages.success(request, '角色创建成功')
        return redirect('role_list')
    
    permissions = Permission.objects.filter(parent__isnull=True).prefetch_related('children')
    return render(request, 'accounts/role_form.html', {'permissions': permissions})


@login_required
def role_edit(request, pk):
    role = Role.objects.get(pk=pk)
    
    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.code = request.POST.get('code')
        role.description = request.POST.get('description')
        role.sort = request.POST.get('sort', 0)
        role.permissions.set(request.POST.getlist('permissions'))
        role.save()
        messages.success(request, '角色更新成功')
        return redirect('role_list')
    
    permissions = Permission.objects.filter(parent__isnull=True).prefetch_related('children')
    return render(request, 'accounts/role_form.html', {'role': role, 'permissions': permissions})


@login_required
def role_delete(request, pk):
    if request.method == 'POST':
        role = Role.objects.get(pk=pk)
        if role.users.exists():
            messages.error(request, '该角色下有用户，无法删除')
        else:
            role.delete()
            messages.success(request, '角色删除成功')
    return redirect('role_list')


def get_permissions(request):
    if not request.user.is_authenticated:
        return JsonResponse({'permissions': []})
    
    permissions = []
    if request.user.is_superuser:
        perms = Permission.objects.filter(is_visible=True)
    else:
        perms = Permission.objects.filter(
            roles__users=request.user,
            is_visible=True
        ).distinct()
    
    for p in perms:
        permissions.append({
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'type': p.type,
            'module': p.module,
        })
    
    return JsonResponse({'permissions': permissions})


def get_menu(request):
    if not request.user.is_authenticated:
        return JsonResponse({'menu': []})
    
    if request.user.is_superuser:
        menus = Permission.objects.filter(type='menu', parent__isnull=True, is_visible=True).prefetch_related('children__children__children')
    else:
        menus = Permission.objects.filter(
            roles__users=request.user,
            type='menu',
            parent__isnull=True,
            is_visible=True
        ).distinct().prefetch_related('children__children__children')
    
    result = []
    for menu in menus:
        item = {
            'id': menu.id,
            'name': menu.name,
            'code': menu.code,
            'children': []
        }
        for child in menu.children.all():
            child_item = {
                'id': child.id,
                'name': child.name,
                'code': child.code,
                'children': []
            }
            for c in child.children.all():
                child_item['children'].append({
                    'id': c.id,
                    'name': c.name,
                    'code': c.code,
                })
            item['children'].append(child_item)
        result.append(item)
    
    return JsonResponse({'menu': result})
