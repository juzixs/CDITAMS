from django.urls import path
from . import views

urlpatterns = [
    # 盘点任务
    path('tasks/', views.task_list, name='inventory_task_list'),
    path('tasks/create/', views.task_create, name='inventory_task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='inventory_task_detail'),
    path('tasks/<int:pk>/execute/', views.task_execute, name='inventory_task_execute'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='inventory_task_delete'),
    path('tasks/<int:pk>/start/', views.task_start, name='inventory_task_start'),
    path('tasks/<int:pk>/complete/', views.task_complete, name='inventory_task_complete'),
    
    # 设备抽选 API
    path('api/tasks/<int:task_id>/random-select/', views.api_random_select, name='api_random_select'),
    path('api/tasks/<int:task_id>/device-search/', views.api_device_search, name='api_device_search'),
    path('api/tasks/<int:task_id>/add-devices/', views.api_add_devices, name='api_add_devices'),
    path('api/tasks/<int:task_id>/remove-device/', views.api_remove_device, name='api_remove_device'),
    
    # 导入设备 API
    path('api/tasks/<int:task_id>/import-devices/', views.api_import_devices, name='api_import_devices'),
    path('api/tasks/<int:task_id>/import-progress/', views.api_import_progress, name='api_import_progress'),
    path('api/tasks/<int:task_id>/manual-parse/', views.api_manual_parse_excel, name='api_manual_parse_excel'),
    
    # AI解析 API
    path('api/ai-parse/', views.api_ai_parse, name='api_ai_parse'),
    path('api/ai-parse-file/', views.api_ai_parse_file, name='api_ai_parse_file'),
    
    # 盘点执行 API
    path('api/tasks/<int:task_id>/device-detail/<int:device_id>/', views.api_device_detail, name='api_device_detail'),
    path('api/tasks/<int:task_id>/check-device/', views.api_check_device, name='api_check_device'),
    path('api/tasks/<int:task_id>/scan-check/', views.api_scan_check, name='api_scan_check'),
    path('api/tasks/<int:task_id>/update-device-info/', views.api_update_device_info, name='api_update_device_info'),
    
    # 盘点报表
    path('report/', views.inventory_report, name='inventory_report'),
    
    # 兼容旧接口（盘点计划）
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/', views.plan_detail, name='plan_detail'),
    
    # 兼容旧URL名称别名
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/verify/', views.task_verify, name='task_verify'),
]
