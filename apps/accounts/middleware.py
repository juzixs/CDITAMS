from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [
            '/login/',
            '/api/permissions/',
            '/api/menu/',
        ]

    def __call__(self, request):
        if request.path in self.exempt_urls or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponseForbidden('{"error": "请先登录"}', content_type='application/json')
            from django.shortcuts import redirect
            return redirect(f'{reverse("login")}?next={request.path}')
        
        return self.get_response(request)
