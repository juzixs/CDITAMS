from django.urls import path
from . import views

urlpatterns = [
    path('configs/', views.config_list, name='config_list'),
    path('configs/<int:pk>/edit/', views.config_edit, name='config_edit'),
    path('org/', views.org_info, name='org_info'),
    path('profile/', views.profile, name='profile'),
    path('data/', views.data_management, name='data_management'),
    path('data/backup/', views.data_backup, name='data_backup'),
    path('data/download/', views.download_backup, name='download_backup'),
]
