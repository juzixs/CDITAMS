from django.db import models
from django.conf import settings
from apps.assets.models import Device, AssetLocation, AssetCategory


class InventoryPlan(models.Model):
    """盘点计划（保留兼容）"""
    PLAN_TYPES = [
        ('full', '全盘'),
        ('sample', '抽盘'),
        ('dynamic', '动态盘点'),
    ]
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending', '待执行'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    name = models.CharField(max_length=128, verbose_name='计划名称')
    plan_no = models.CharField(max_length=32, unique=True, verbose_name='计划编号')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, verbose_name='计划类型')
    scope = models.TextField(blank=True, verbose_name='盘点范围描述')
    location_ids = models.TextField(blank=True, verbose_name='涉及位置ID列表')
    category_ids = models.TextField(blank=True, verbose_name='涉及分类ID列表')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    scheduled_start = models.DateTimeField(verbose_name='计划开始时间')
    scheduled_end = models.DateTimeField(verbose_name='计划结束时间')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_plans', verbose_name='创建人')
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'inventory_plans'
        verbose_name = '盘点计划'
        verbose_name_plural = '盘点计划'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.plan_no} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.plan_no:
            from django.utils import timezone
            last_plan = InventoryPlan.objects.order_by('-id').first()
            next_no = int(last_plan.id or 0) + 1 if last_plan else 1
            self.plan_no = f"IP{timezone.now().strftime('%Y%m%d')}{next_no:04d}"
        super().save(*args, **kwargs)


class InventoryTask(models.Model):
    """盘点任务"""
    TASK_TYPES = [
        ('full', '全盘'),
        ('sample', '抽盘'),
        ('dynamic', '动态盘点'),
    ]
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('in_progress', '执行中'),
        ('completed', '已完成'),
    ]
    
    plan = models.ForeignKey(InventoryPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name='盘点计划')
    task_no = models.CharField(max_length=32, unique=True, verbose_name='任务编号')
    name = models.CharField(max_length=128, blank=True, verbose_name='任务名称')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='full', verbose_name='任务类型')
    is_fixed_only = models.BooleanField(default=False, verbose_name='仅固资在账')
    location = models.ForeignKey(AssetLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_tasks', verbose_name='盘点位置')
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_tasks', verbose_name='盘点分类')
    device_count = models.IntegerField(default=0, verbose_name='应盘数量')
    checked_count = models.IntegerField(default=0, verbose_name='已盘数量')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_tasks', verbose_name='负责人')
    scheduled_start = models.DateTimeField(null=True, blank=True, verbose_name='计划开始时间')
    scheduled_end = models.DateTimeField(null=True, blank=True, verbose_name='计划结束时间')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks', verbose_name='创建人')
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'inventory_tasks'
        verbose_name = '盘点任务'
        verbose_name_plural = '盘点任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_no} - {self.name or self.get_task_type_display()}"

    def save(self, *args, **kwargs):
        if not self.task_no:
            from django.utils import timezone
            last_task = InventoryTask.objects.order_by('-id').first()
            next_no = (int(last_task.id) + 1) if last_task else 1
            self.task_no = f"IT{timezone.now().strftime('%Y%m%d')}{next_no:04d}"
        super().save(*args, **kwargs)


class InventoryTaskDevice(models.Model):
    """盘点任务设备（待盘点设备列表）"""
    STATUS_CHOICES = [
        ('pending', '待盘点'),
        ('checked', '已盘点'),
    ]
    
    task = models.ForeignKey(InventoryTask, on_delete=models.CASCADE, related_name='task_devices', verbose_name='盘点任务')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='inventory_task_devices', verbose_name='设备')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    sort_order = models.IntegerField(default=0, verbose_name='排序序号')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='添加人')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name='盘点时间')

    class Meta:
        db_table = 'inventory_task_devices'
        verbose_name = '盘点任务设备'
        verbose_name_plural = '盘点任务设备'
        ordering = ['sort_order', 'id']
        unique_together = ['task', 'device']

    def __str__(self):
        return f"{self.task.task_no} - {self.device.asset_no}"


class InventoryRecord(models.Model):
    """盘点记录"""
    LOCATION_STATUS = [
        ('in_place', '在位'),
        ('moved', '搬离'),
    ]
    ASSET_STATUS = [
        ('normal', '正常'),
        ('damaged', '损坏'),
    ]
    SOURCES = [
        ('manual', '手工盘点'),
        ('scan', '扫码盘点'),
        ('wechat', '微信扫码'),
    ]
    
    task = models.ForeignKey(InventoryTask, on_delete=models.CASCADE, related_name='records', verbose_name='盘点任务')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='inventory_records', verbose_name='设备')
    task_device = models.ForeignKey(InventoryTaskDevice, on_delete=models.SET_NULL, null=True, blank=True, related_name='records', verbose_name='任务设备关联')
    device_status = models.CharField(max_length=20, blank=True, verbose_name='盘点时设备状态')
    location_status = models.CharField(max_length=20, choices=LOCATION_STATUS, default='in_place', verbose_name='位置状态')
    asset_status = models.CharField(max_length=20, choices=ASSET_STATUS, default='normal', verbose_name='资产状态')
    remarks = models.TextField(blank=True, verbose_name='备注')
    photo_path = models.CharField(max_length=256, blank=True, verbose_name='现场照片路径')
    photo = models.ImageField(upload_to='inventory_photos/', blank=True, verbose_name='现场照片')
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name='盘点时间')
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_records', verbose_name='盘点人')
    source = models.CharField(max_length=20, choices=SOURCES, default='manual', verbose_name='来源')

    class Meta:
        db_table = 'inventory_records'
        verbose_name = '盘点记录'
        verbose_name_plural = '盘点记录'
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.task.task_no} - {self.device.asset_no}"
