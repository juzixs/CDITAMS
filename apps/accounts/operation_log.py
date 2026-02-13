import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('operation')


class OperationLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass
    
    def process_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.method in ['POST', 'PUT', 'DELETE']:
                from apps.logs.models import SystemLog
                import json
                
                excluded_urls = ['/admin/', '/api/']
                if any(request.path.startswith(url) for url in excluded_urls):
                    return response
                
                try:
                    request_data = ''
                    if hasattr(request, 'POST') and request.POST:
                        safe_data = dict(request.POST)
                        if 'password' in safe_data:
                            safe_data['password'] = '***'
                        request_data = json.dumps(safe_data, ensure_ascii=False)[:500]
                    
                    module = self._get_module(request.path)
                    
                    SystemLog.objects.create(
                        user=request.user,
                        username=request.user.emp_no,
                        log_type='operation',
                        action=self._get_action(request),
                        module=module,
                        method=request.method,
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        request_url=request.path[:500],
                        request_data=request_data,
                        response_status=response.status_code if hasattr(response, 'status_code') else None,
                    )
                except Exception:
                    pass
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_module(self, path):
        if '/assets/' in path:
            return '资产管理'
        elif '/inventory/' in path:
            return '盘点管理'
        elif '/users/' in path or '/departments/' in path or '/roles/' in path:
            return '组织管理'
        elif '/todos/' in path:
            return '待办管理'
        elif '/settings/' in path:
            return '系统设置'
        elif '/logs/' in path:
            return '日志管理'
        return '其他'
    
    def _get_action(self, request):
        action_map = {
            ('POST', 'create'): '创建',
            ('POST', 'add'): '创建',
            ('POST', 'add'): '创建',
            ('PUT', 'edit'): '更新',
            ('POST', 'edit'): '更新',
            ('POST', 'update'): '更新',
            ('DELETE', 'delete'): '删除',
            ('POST', 'delete'): '删除',
            ('POST', 'login'): '登录',
            ('POST', 'logout'): '登出',
        }
        return action_map.get((request.method, request.path.split('/')[-2]), f'{request.method}操作')
