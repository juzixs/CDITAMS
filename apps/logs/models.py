from django.db import models
from django.conf import settings


class SystemLog(models.Model):
    TYPE_CHOICES = [
        ('login', '登录'),
        ('logout', '登出'),
        ('operation', '操作'),
        ('error', '错误'),
        ('security', '安全'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作用户')
    username = models.CharField(max_length=64, verbose_name='操作账号')
    log_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='日志类型')
    action = models.CharField(max_length=128, verbose_name='操作动作')
    module = models.CharField(max_length=64, blank=True, verbose_name='操作模块')
    method = models.CharField(max_length=32, blank=True, verbose_name='请求方法')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    request_url = models.CharField(max_length=512, blank=True, verbose_name='请求URL')
    request_data = models.TextField(blank=True, verbose_name='请求参数')
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'system_logs'
        verbose_name = '系统日志'
        verbose_name_plural = '系统日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['log_type']),
        ]

    def __str__(self):
        return f"{self.username} - {self.action}"


class SystemAssetLog(models.Model):
    ACTIONS = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('assign', '分配'),
        ('transfer', '转移'),
        ('repair', '维修'),
        ('scrap', '报废'),
    ]
    
    device = models.ForeignKey('assets.Device', on_delete=models.CASCADE, related_name='sys_logs', verbose_name='设备')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    action = models.CharField(max_length=20, choices=ACTIONS, verbose_name='操作')
    field_name = models.CharField(max_length=64, blank=True, verbose_name='变动字段')
    old_value = models.TextField(blank=True, verbose_name='旧值')
    new_value = models.TextField(blank=True, verbose_name='新值')
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'asset_sys_logs'
        verbose_name = '资产变动日志'
        verbose_name_plural = '资产变动日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['device', '-created_at']),
        ]

    def __str__(self):
        return f"{self.device.asset_no} - {self.action}"
