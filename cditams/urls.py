from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('assets/', include('apps.assets.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('todos/', include('apps.todos.urls')),
    path('logs/', include('apps.logs.urls')),
    path('settings/', include('apps.settings.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
