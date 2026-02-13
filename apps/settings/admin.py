from django.contrib import admin
from .models import SystemConfig, Organization


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ['config_key', 'config_value', 'value_type', 'config_group', 'is_system']
    list_filter = ['config_group', 'value_type']
    search_fields = ['config_key', 'description']


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'code', 'contact_person', 'contact_phone']
