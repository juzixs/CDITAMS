from django.contrib import admin
from .models import Todo, Notification


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ['title', 'todo_type', 'priority', 'status', 'assignee', 'due_date', 'created_at']
    list_filter = ['status', 'priority', 'todo_type']
    search_fields = ['title', 'content']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type']
    search_fields = ['title', 'content']
