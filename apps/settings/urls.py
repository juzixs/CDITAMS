from django.urls import path
from . import views

urlpatterns = [
    path('configs/', views.config_list, name='config_list'),
    path('configs/save/', views.config_save, name='config_save'),
    path('org/', views.org_info, name='org_info'),
    path('profile/', views.profile, name='profile'),
    path('data/', views.data_management, name='data_management'),
    path('data/backup/', views.data_backup, name='data_backup'),
    path('data/download/', views.download_backup, name='download_backup'),
    path('data/delete/', views.delete_backup, name='delete_backup'),
]
