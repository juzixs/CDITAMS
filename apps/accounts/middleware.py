from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class LoginRequiredMiddleware:
    """登录检查中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            '/login/',
            '/api/permissions/',
            '/api/menu/',
            '/assets/view/',
            '/assets/api/map-data/',
            '/assets/device/scan/',
        ]

    def __call__(self, request):
        if any(request.path.startswith(url) for url in self.exempt_urls) or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponseForbidden('{"error": "请先登录"}', content_type='application/json')
            from django.shortcuts import redirect
            return redirect(f'{reverse("login")}?next={request.path}')
        
        return self.get_response(request)


class PermissionMiddleware(MiddlewareMixin):
    """
    权限中间件
    将用户权限列表传递到模板上下文
    """
    
    def process_request(self, request):
        """处理请求，初始化用户权限"""
        if request.user.is_authenticated:
            request.user_permissions = self._get_user_permissions(request.user)
        else:
            request.user_permissions = []
    
    def _get_user_permissions(self, user):
        """获取用户权限列表"""
        from apps.accounts.models import Permission
        
        # 超级管理员或拥有superuser/admin角色的用户拥有所有权限
        if user.is_superuser:
            return list(Permission.objects.values_list('code', flat=True))
        
        # 检查是否是超级管理员或管理员角色
        if user.role and user.role.code in ('superuser', 'admin'):
            return list(Permission.objects.values_list('code', flat=True))
        
        # 普通用户从角色获取权限
        if user.role:
            return list(user.role.permissions.values_list('code', flat=True))
        
        return []
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """在视图执行前处理，将权限添加到请求对象"""
        # 权限已经在process_request中处理
        return None
    
    def process_template_response(self, request, response):
        """处理模板响应，将权限添加到上下文"""
        if hasattr(response, 'context_data') and response.context_data is not None:
            user_permissions = getattr(request, 'user_permissions', [])
            response.context_data['user_permissions'] = user_permissions
            response.context_data['user_perm_set'] = set(user_permissions)
        
        return response
