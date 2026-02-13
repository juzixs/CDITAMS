from django.contrib import admin
from .models import (
    Device, AssetCategory, AssetLocation, DeviceField, DeviceFieldValue,
    Workstation, MapElement, MapBackground,
    Software, SoftwareCategory, SoftwareLicense,
    Consumable, ConsumableCategory, ConsumableRecord,
    ServiceType, ServiceRequest, ServiceLog, AssetLog
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'sort']
    list_filter = ['parent']
    search_fields = ['name', 'code']


@admin.register(AssetLocation)
class AssetLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'level', 'parent', 'sort']
    list_filter = ['level', 'parent']
    search_fields = ['name', 'code']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['asset_no', 'name', 'category', 'status', 'user', 'location', 'created_at']
    list_filter = ['status', 'category', 'location']
    search_fields = ['asset_no', 'name', 'serial_no', 'device_no']
    ordering = ['-created_at']


@admin.register(DeviceField)
class DeviceFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_key', 'field_type', 'category', 'is_required', 'sort']
    list_filter = ['field_type', 'category']
    search_fields = ['name', 'field_key']


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'version', 'vendor', 'license_type', 'license_count']
    list_filter = ['license_type', 'category']
    search_fields = ['name', 'vendor']


@admin.register(Consumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'code', 'stock_quantity', 'min_stock', 'unit', 'price']
    list_filter = ['category']
    search_fields = ['name', 'code']


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['request_no', 'title', 'service_type', 'priority', 'status', 'requester', 'created_at']
    list_filter = ['status', 'priority', 'service_type']
    search_fields = ['request_no', 'title']
    ordering = ['-created_at']


@admin.register(AssetLog)
class AssetLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'user', 'action', 'field_name', 'created_at']
    list_filter = ['action']
    search_fields = ['device__asset_no']
    ordering = ['-created_at']
