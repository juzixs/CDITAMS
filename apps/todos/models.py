from django.db import models
from django.conf import settings


class Todo(models.Model):
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    TYPE_CHOICES = [
        ('personal', '个人待办'),
        ('asset_approval', '资产审批'),
        ('maintenance', '维修审批'),
        ('inventory', '盘点任务'),
        ('transfer', '资产调拨'),
    ]
    
    title = models.CharField(max_length=256, verbose_name='待办标题')
    content = models.TextField(blank=True, verbose_name='待办内容')
    todo_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default='personal', verbose_name='待办类型')
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    remind_time = models.DateTimeField(null=True, blank=True, verbose_name='提醒时间')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='todos', verbose_name='待办人')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_todos', verbose_name='创建人')
    related_type = models.CharField(max_length=32, blank=True, verbose_name='关联类型')
    related_id = models.IntegerField(null=True, blank=True, verbose_name='关联ID')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'todos'
        verbose_name = '待办事项'
        verbose_name_plural = '待办事项'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Notification(models.Model):
    TYPE_CHOICES = [
        ('system', '系统通知'),
        ('todo', '待办提醒'),
        ('approval', '审批通知'),
        ('inventory', '盘点通知'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', verbose_name='接收人')
    title = models.CharField(max_length=256, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    notification_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default='system', verbose_name='通知类型')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='阅读时间')
    related_type = models.CharField(max_length=32, blank=True, verbose_name='关联类型')
    related_id = models.IntegerField(null=True, blank=True, verbose_name='关联ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'notifications'
        verbose_name = '通知消息'
        verbose_name_plural = '通知消息'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
