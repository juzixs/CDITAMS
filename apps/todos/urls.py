from django.urls import path
from . import views

urlpatterns = [
    path('', views.todo_list, name='todo_list'),
    path('create/', views.todo_create, name='todo_create'),
    path('<int:pk>/edit/', views.todo_edit, name='todo_edit'),
    path('<int:pk>/complete/', views.todo_complete, name='todo_complete'),
    path('<int:pk>/delete/', views.todo_delete, name='todo_delete'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_read, name='notification_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('api/count/', views.api_notification_count, name='api_notification_count'),
]
