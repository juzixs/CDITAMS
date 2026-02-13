from django.contrib import admin
from .models import InventoryPlan, InventoryTask, InventoryRecord


@admin.register(InventoryPlan)
class InventoryPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_no', 'name', 'plan_type', 'status', 'scheduled_start', 'scheduled_end', 'creator']
    list_filter = ['plan_type', 'status']
    search_fields = ['plan_no', 'name']


@admin.register(InventoryTask)
class InventoryTaskAdmin(admin.ModelAdmin):
    list_display = ['task_no', 'plan', 'location', 'status', 'device_count', 'checked_count', 'assignee']
    list_filter = ['status', 'plan']
    search_fields = ['task_no']


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ['task', 'device', 'location_status', 'asset_status', 'checked_by', 'checked_at']
    list_filter = ['location_status', 'asset_status', 'source']
    search_fields = ['device__asset_no']
