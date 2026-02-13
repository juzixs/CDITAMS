from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class Department(models.Model):
    name = models.CharField(max_length=64, verbose_name='部门名称')
    code = models.CharField(max_length=32, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级部门')
    description = models.TextField(blank=True, verbose_name='部门描述')
    sort = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'departments'
        verbose_name = '部门'
        verbose_name_plural = '部门'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name

    def get_full_path(self):
        paths = []
        current = self
        while current:
            paths.insert(0, current.name)
            current = current.parent
        return ' / '.join(paths)


class User(AbstractUser):
    GENDER_CHOICES = [('male', '男'), ('female', '女')]
    
    emp_no = models.CharField(max_length=32, unique=True, verbose_name='工号')
    realname = models.CharField(max_length=64, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name='性别')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name='所属部门')
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name='所属角色')
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='头像')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['emp_no']

    def __str__(self):
        return f"{self.emp_no} - {self.realname}"


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name='角色名称')
    code = models.CharField(max_length=32, unique=True, verbose_name='角色标识')
    description = models.TextField(blank=True, verbose_name='角色描述')
    permissions = models.ManyToManyField('Permission', blank=True, related_name='roles', verbose_name='权限')
    sort = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'roles'
        verbose_name = '角色'
        verbose_name_plural = '角色'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class Permission(models.Model):
    TYPE_CHOICES = [('menu', '菜单权限'), ('button', '按钮权限')]
    
    name = models.CharField(max_length=64, verbose_name='权限名称')
    code = models.CharField(max_length=64, unique=True, verbose_name='权限标识')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='menu', verbose_name='权限类型')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级权限')
    module = models.CharField(max_length=32, blank=True, verbose_name='所属模块')
    sort = models.IntegerField(default=0, verbose_name='排序')
    is_visible = models.BooleanField(default=True, verbose_name='是否显示')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'permissions'
        verbose_name = '权限'
        verbose_name_plural = '权限'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_logs', verbose_name='用户')
    username = models.CharField(max_length=64, verbose_name='用户名')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    action = models.CharField(max_length=20, verbose_name='操作')
    message = models.CharField(max_length=256, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='登录时间')

    class Meta:
        db_table = 'login_logs'
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} - {self.action}"
