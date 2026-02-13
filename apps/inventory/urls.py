from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/', views.plan_detail, name='plan_detail'),
    path('plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:pk>/delete/', views.plan_delete, name='plan_delete'),
    path('plans/<int:pk>/generate-tasks/', views.plan_generate_tasks, name='plan_generate_tasks'),
    path('plans/<int:pk>/start/', views.plan_start, name='plan_start'),
    path('plans/<int:pk>/complete/', views.plan_complete, name='plan_complete'),
    
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/execute/', views.task_execute, name='task_execute'),
    path('tasks/<int:pk>/assign/', views.task_assign, name='task_assign'),
    path('tasks/<int:pk>/verify/', views.task_verify, name='task_verify'),
    
    path('report/', views.inventory_report, name='inventory_report'),
    
    path('api/scan-device/', views.api_scan_device, name='api_scan_device'),
    path('api/record-device/', views.api_record_device, name='api_record_device'),
]
