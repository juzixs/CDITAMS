from django.contrib import admin
from .models import SystemLog, SystemAssetLog


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'log_type', 'action', 'module', 'ip_address', 'created_at']
    list_filter = ['log_type', 'module']
    search_fields = ['username', 'action', 'ip_address']
    ordering = ['-created_at']


@admin.register(SystemAssetLog)
class SystemAssetLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'user', 'action', 'field_name', 'created_at']
    list_filter = ['action']
    search_fields = ['device__asset_no', 'device__name']
    ordering = ['-created_at']
