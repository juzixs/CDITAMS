from django.db import models


class SystemConfig(models.Model):
    TYPE_CHOICES = [
        ('string', '字符串'),
        ('int', '整数'),
        ('boolean', '布尔值'),
        ('json', 'JSON'),
    ]
    GROUP_CHOICES = [
        ('basic', '基础设置'),
        ('security', '安全设置'),
        ('asset', '资产设置'),
        ('wechat', '微信设置'),
    ]
    
    config_key = models.CharField(max_length=64, unique=True, verbose_name='配置键')
    config_value = models.TextField(blank=True, verbose_name='配置值')
    value_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default='string', verbose_name='值类型')
    config_group = models.CharField(max_length=32, choices=GROUP_CHOICES, default='basic', verbose_name='配置分组')
    description = models.CharField(max_length=256, blank=True, verbose_name='说明')
    is_system = models.BooleanField(default=False, verbose_name='系统级配置')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'system_configs'
        verbose_name = '系统配置'
        verbose_name_plural = '系统配置'
        ordering = ['config_group', 'id']

    def __str__(self):
        return self.config_key


class Organization(models.Model):
    name = models.CharField(max_length=128, verbose_name='企业名称')
    short_name = models.CharField(max_length=64, blank=True, verbose_name='简称')
    code = models.CharField(max_length=32, unique=True, verbose_name='企业编码')
    logo = models.ImageField(upload_to='org_logos/', blank=True, verbose_name='Logo')
    contact_person = models.CharField(max_length=64, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    contact_email = models.EmailField(blank=True, verbose_name='联系邮箱')
    address = models.CharField(max_length=256, blank=True, verbose_name='地址')
    website = models.CharField(max_length=128, blank=True, verbose_name='网站')
    description = models.TextField(blank=True, verbose_name='简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'organizations'
        verbose_name = '企业信息'
        verbose_name_plural = '企业信息'

    def __str__(self):
        return self.name
