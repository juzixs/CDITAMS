"""
权限检查装饰器
用于在视图函数级别进行细粒度权限控制
"""

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def permission_required(*permission_codes):
    """
    权限检查装饰器
    
    使用方式:
    @permission_required('device_create')
    def device_create(request):
        ...
    
    @permission_required('device_edit', 'device_view')  # 需要任一权限
    def device_edit(request, pk):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # 未登录用户重定向到登录页
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': '请先登录', 'code': 401}, status=401)
                return redirect('login')
            
            # 超级管理员拥有所有权限
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # 获取用户权限列表
            user_permissions = get_user_permissions(request.user)
            
            # 检查是否拥有所需权限（任一权限即可）
            has_permission = any(perm in user_permissions for perm in permission_codes)
            
            if not has_permission:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': '没有权限执行此操作', 'code': 403}, status=403)
                messages.error(request, '没有权限执行此操作')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required_all(*permission_codes):
    """
    权限检查装饰器（需要所有权限）
    
    使用方式:
    @permission_required_all('device_view', 'device_edit')
    def device_edit(request, pk):
        ...  # 需要同时拥有device_view和device_edit权限
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': '请先登录', 'code': 401}, status=401)
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            user_permissions = get_user_permissions(request.user)
            
            # 检查是否拥有所有所需权限
            has_permission = all(perm in user_permissions for perm in permission_codes)
            
            if not has_permission:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': '没有权限执行此操作', 'code': 403}, status=403)
                messages.error(request, '没有权限执行此操作')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_user_permissions(user):
    """获取用户的权限代码列表"""
    if hasattr(user, '_cached_permissions'):
        return user._cached_permissions
    
    from apps.accounts.models import Permission
    # 超级管理员或拥有superuser/admin角色的用户拥有所有权限
    if user.is_superuser or (user.role and user.role.code in ('superuser', 'admin')):
        perms = list(Permission.objects.values_list('code', flat=True))
    else:
        perms = list(user.get_permissions())
    
    user._cached_permissions = perms
    return perms


def has_permission(user, *permission_codes):
    """
    检查用户是否拥有指定权限（用于模板和业务逻辑）
    
    使用方式:
    if has_permission(request.user, 'device_create'):
        ...
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in permission_codes)


def has_permission_all(user, *permission_codes):
    """检查用户是否拥有所有指定权限"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    user_permissions = get_user_permissions(user)
    return all(perm in user_permissions for perm in permission_codes)
