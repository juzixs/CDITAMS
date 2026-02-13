from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_log_list, name='login_log_list'),
    path('operation/', views.operation_log_list, name='operation_log_list'),
    path('asset/', views.asset_log_list, name='asset_log_list'),
]
