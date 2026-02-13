from django.urls import path
from . import views

urlpatterns = [
    path('', views.device_list, name='device_list'),
    path('create/', views.device_create, name='device_create'),
    path('<int:pk>/', views.device_detail, name='device_detail'),
    path('<int:pk>/edit/', views.device_edit, name='device_edit'),
    path('<int:pk>/delete/', views.device_delete, name='device_delete'),
    path('<int:pk>/print/', views.device_print_label, name='device_print_label'),
    path('scan/<int:device_id>/', views.device_scan, name='device_scan'),
    path('batch/delete/', views.device_batch_delete, name='device_batch_delete'),
    path('batch/assign/', views.device_batch_assign, name='device_batch_assign'),
    path('batch/fault/', views.device_batch_fault, name='device_batch_fault'),
    path('batch/scrap/', views.device_batch_scrap, name='device_batch_scrap'),
    path('api/get-code/', views.api_get_code, name='api_get_code'),
    path('api/stats/', views.device_stats, name='device_stats'),
    path('api/device-bind-workstation/', views.api_device_bind_workstation, name='api_device_bind_workstation'),
    
    path('api/categories/', views.api_category_list, name='api_category_list'),
    path('api/categories/save/', views.api_category_save, name='api_category_save'),
    path('api/categories/<int:id>/', views.api_category_delete, name='api_category_delete'),
    path('api/devices/generate-asset-number/', views.api_generate_asset_number, name='api_generate_asset_number'),
    
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:pk>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),
    path('map/', views.device_map, name='device_map'),
    path('locations/<int:pk>/map/', views.location_map, name='location_map'),
    path('locations/<int:pk>/map/edit/', views.location_map, name='location_map_edit'),
    path('api/location-tree/', views.location_tree, name='api_location_tree'),
    path('api/map-data/<int:pk>/', views.map_data, name='api_map_data'),
    
    path('locations/<int:pk>/workstations/', views.workstation_list, name='workstation_list'),
    path('workstations/create/', views.workstation_create, name='workstation_create'),
    path('workstations/<int:pk>/edit/', views.workstation_edit, name='workstation_edit'),
    path('workstations/<int:pk>/delete/', views.workstation_delete, name='workstation_delete'),
    path('workstations/batch-create/', views.workstation_batch_create, name='workstation_batch_create'),
    
    path('locations/<int:pk>/elements/save/', views.map_element_save, name='map_element_save'),
    path('elements/<int:pk>/delete/', views.map_element_delete, name='map_element_delete'),
    path('locations/<int:pk>/background/upload/', views.map_background_upload, name='map_background_upload'),
    
    path('locations/<int:pk>/area-binding/', views.location_area_binding, name='location_area_binding'),
    path('locations/<int:pk>/area-binding/<int:binding_id>/delete/', views.location_area_binding_delete, name='location_area_binding_delete'),
    path('api/locations/<int:pk>/area-bindings/', views.api_location_area_bindings, name='api_location_area_bindings'),
    
    path('fields/', views.field_list, name='field_list'),
    path('fields/create/', views.field_create, name='field_create'),
    path('fields/<int:pk>/edit/', views.field_edit, name='field_edit'),
    path('fields/<int:pk>/delete/', views.field_delete, name='field_delete'),
    
    path('software/', views.software_list, name='software_list'),
    path('software/create/', views.software_create, name='software_create'),
    
    path('consumables/', views.consumable_list, name='consumable_list'),
    path('consumables/create/', views.consumable_create, name='consumable_create'),
    
    path('services/', views.service_list, name='service_list'),
    path('services/create/', views.service_create, name='service_create'),
]
