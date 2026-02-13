from django.contrib import admin
from .models import Department, User, Role, Permission, LoginLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'sort', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'code']
    ordering = ['sort', 'id']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['emp_no', 'realname', 'gender', 'department', 'role', 'is_active', 'created_at']
    list_filter = ['is_active', 'department', 'role', 'gender']
    search_fields = ['emp_no', 'realname', 'phone', 'email']
    ordering = ['emp_no']
    fieldsets = [
        ('基本信息', {'fields': ('username', 'emp_no', 'realname', 'gender', 'password')}),
        ('联系方式', {'fields': ('email', 'phone', 'avatar')}),
        ('组织信息', {'fields': ('department', 'role')}),
        ('状态', {'fields': ('is_active', 'is_superuser')}),
    ]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sort', 'created_at']
    search_fields = ['name', 'code']
    filter_horizontal = ['permissions']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'type', 'module', 'parent', 'sort']
    list_filter = ['type', 'module']
    search_fields = ['name', 'code']
    ordering = ['sort', 'id']


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'action', 'ip_address', 'message', 'created_at']
    list_filter = ['action']
    search_fields = ['username', 'ip_address']
    ordering = ['-created_at']
