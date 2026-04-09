from django.conf import settings
import re


class CSRFOriginMiddleware:
    """自动从数据库加载 app_url 并添加到 CSRF 可信源"""

    def __init__(self, get_response):
        self.get_response = get_response
        self._loaded = False

    def __call__(self, request):
        if not self._loaded:
            self._load_csrf_origins()
            self._loaded = True
        return self.get_response(request)

    def _load_csrf_origins(self):
        """从数据库加载 app_url 并添加到 CSRF 可信源"""
        try:
            from apps.settings.models import SystemConfig
            app_url = SystemConfig.objects.filter(config_key='app_url').first()
            if app_url and app_url.config_value:
                url = app_url.config_value.strip()
                match = re.match(r'https?://([^/]+)', url)
                if match:
                    origin = match.group(1)
                    current_origins = list(getattr(settings, 'CSRF_TRUSTED_ORIGINS', []))
                    if origin not in current_origins:
                        settings.CSRF_TRUSTED_ORIGINS = current_origins + [origin]
        except Exception:
            pass
