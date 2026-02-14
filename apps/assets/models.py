from django.db import models
from django.conf import settings


class AssetCategory(models.Model):
    name = models.CharField(max_length=64, verbose_name='分类名称')
    code = models.CharField(max_length=32, verbose_name='分类编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级分类')
    level = models.IntegerField(default=1, choices=[(i, f'{i}级') for i in range(1, 5)], verbose_name='分类级别')
    description = models.TextField(blank=True, verbose_name='分类描述')
    sort = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'asset_categories'
        verbose_name = '资产分类'
        verbose_name_plural = '资产分类'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name

    def get_full_code(self):
        codes = []
        current = self
        while current:
            codes.insert(0, current.code)
            current = current.parent
        return '-'.join(codes)

    @classmethod
    def find_by_asset_prefix(cls, asset_prefix):
        parts = asset_prefix.split('-')
        if len(parts) < 1 or not parts[0]:
            return None
        
        current_level = 1
        current_category = None
        
        for i, part in enumerate(parts):
            if current_level == 1:
                current_category = cls.objects.filter(code=part, level=1).first()
            else:
                if current_category:
                    current_category = cls.objects.filter(code=part, parent=current_category, level=current_level).first()
            
            if not current_category:
                break
            current_level += 1
        
        return current_category


class AssetLocation(models.Model):
    name = models.CharField(max_length=64, verbose_name='位置名称')
    code = models.CharField(max_length=32, unique=True, verbose_name='位置编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级位置')
    level = models.IntegerField(default=1, choices=[(i, f'{i}级') for i in range(1, 5)], verbose_name='位置级别')
    park_code = models.CharField(max_length=2, blank=True, verbose_name='园区编码')
    building_code = models.CharField(max_length=2, blank=True, verbose_name='设施编码')
    floor_code = models.CharField(max_length=2, blank=True, verbose_name='楼层编码')
    floor_count = models.IntegerField(default=1, verbose_name='地上楼层数')
    basement_count = models.IntegerField(default=0, verbose_name='地下楼层数')
    has_rooftop = models.BooleanField(default=False, verbose_name='包含天台')
    room_code = models.CharField(max_length=20, blank=True, verbose_name='房间编码')
    has_map = models.BooleanField(default=False, verbose_name='是否有地图')
    map_width = models.IntegerField(default=1200, verbose_name='地图宽度')
    map_height = models.IntegerField(default=800, verbose_name='地图高度')
    grid_size = models.IntegerField(default=50, verbose_name='网格大小')
    default_doorstop_width = models.FloatField(default=15, verbose_name='默认门垛宽度')
    default_snap_threshold = models.FloatField(default=10, verbose_name='默认吸附阈值')
    default_snap_enabled = models.BooleanField(default=True, verbose_name='默认启用吸附')
    description = models.TextField(blank=True, verbose_name='位置描述')
    sort = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'asset_locations'
        verbose_name = '资产位置'
        verbose_name_plural = '资产位置'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        return self.get_full_path()

    def get_full_path(self):
        paths = []
        current = self
        while current:
            paths.insert(0, current.name)
            current = current.parent
        return ' / '.join(paths)

    def get_level_display_class(self):
        level_names = {1: '园区', 2: '设施', 3: '楼层', 4: '房间'}
        return level_names.get(self.level, '')


class LocationAreaBinding(models.Model):
    location = models.ForeignKey(AssetLocation, on_delete=models.CASCADE, related_name='area_bindings', verbose_name='4级位置')
    parent_location = models.ForeignKey(AssetLocation, on_delete=models.CASCADE, related_name='child_area_bindings', verbose_name='3级位置')
    area_points = models.TextField(verbose_name='区域坐标点(JSON)')
    area_color = models.CharField(max_length=7, default='#3498db', verbose_name='区域颜色')
    area_name = models.CharField(max_length=64, verbose_name='区域名称')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'location_area_bindings'
        verbose_name = '位置区域绑定'
        verbose_name_plural = '位置区域绑定'

    def __str__(self):
        return f"{self.parent_location.name} - {self.area_name}"


class DeviceField(models.Model):
    TYPE_CHOICES = [
        ('text', '文本'),
        ('textarea', '多行文本'),
        ('number', '数字'),
        ('select', '下拉选择'),
        ('multi_select', '多选'),
        ('date', '日期'),
        ('datetime', '日期时间'),
        ('checkbox', '复选框'),
        ('file', '文件上传'),
    ]
    
    name = models.CharField(max_length=64, verbose_name='字段名称')
    field_key = models.CharField(max_length=32, unique=True, verbose_name='字段键名')
    field_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text', verbose_name='字段类型')
    category = models.ForeignKey(AssetCategory, on_delete=models.CASCADE, null=True, blank=True, related_name='fields', verbose_name='所属分类')
    is_required = models.BooleanField(default=False, verbose_name='是否必填')
    is_visible = models.BooleanField(default=True, verbose_name='是否可见')
    options = models.TextField(blank=True, verbose_name='选项(JSON)')
    default_value = models.CharField(max_length=256, blank=True, verbose_name='默认值')
    sort = models.IntegerField(default=0, verbose_name='排序')
    is_system = models.BooleanField(default=False, verbose_name='系统字段')

    class Meta:
        db_table = 'device_fields'
        verbose_name = '设备字段'
        verbose_name_plural = '设备字段'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class DeviceFieldValue(models.Model):
    device = models.ForeignKey('Device', on_delete=models.CASCADE, related_name='field_values', verbose_name='设备')
    field = models.ForeignKey(DeviceField, on_delete=models.CASCADE, verbose_name='字段')
    value = models.TextField(blank=True, verbose_name='字段值')

    class Meta:
        db_table = 'device_field_values'
        verbose_name = '设备字段值'
        verbose_name_plural = '设备字段值'


class Device(models.Model):
    STATUS_CHOICES = [
        ('normal', '正常'),
        ('fault', '故障'),
        ('repairing', '维修中'),
        ('scrapped', '已报废'),
        ('unused', '闲置'),
    ]
    
    SECRET_LEVELS = [
        ('public', '公开'),
        ('internal', '内部'),
        ('confidential', '机密'),
        ('secret', '绝密'),
    ]
    
    asset_no = models.CharField(max_length=64, unique=True, verbose_name='资产编号')
    device_no = models.CharField(max_length=64, blank=True, verbose_name='设备编号')
    serial_no = models.CharField(max_length=128, blank=True, verbose_name='序列号')
    name = models.CharField(max_length=128, verbose_name='设备名称')
    model = models.CharField(max_length=128, blank=True, verbose_name='型号')
    brand = models.CharField(max_length=64, blank=True, verbose_name='品牌')
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='devices', verbose_name='资产分类')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='normal', verbose_name='设备状态')
    secret_level = models.CharField(max_length=20, choices=SECRET_LEVELS, default='public', verbose_name='密级')
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices', verbose_name='使用人')
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices', verbose_name='所属部门')
    location = models.ForeignKey(AssetLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='devices', verbose_name='所在位置')
    workstation = models.ForeignKey('Workstation', on_delete=models.SET_NULL, null=True, blank=True, related_name='devices', verbose_name='工位')
    location_text = models.CharField(max_length=256, blank=True, verbose_name='位置文字描述')
    
    purchase_date = models.DateField(null=True, blank=True, verbose_name='购入日期')
    enable_date = models.DateField(null=True, blank=True, verbose_name='启用时间')
    install_date = models.DateField(null=True, blank=True, verbose_name='安装时间')
    
    mac_address = models.CharField(max_length=64, blank=True, verbose_name='MAC地址')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    os_name = models.CharField(max_length=64, blank=True, verbose_name='操作系统')
    os_version = models.CharField(max_length=64, blank=True, verbose_name='系统版本')
    
    disk_serial = models.CharField(max_length=128, blank=True, verbose_name='硬盘序列号')
    purpose = models.CharField(max_length=256, blank=True, verbose_name='用途')
    remarks = models.TextField(blank=True, verbose_name='备注')
    
    is_fixed = models.BooleanField(default=False, verbose_name='固资在账')
    asset_card_no = models.CharField(max_length=64, blank=True, verbose_name='卡片编号')
    is_secret = models.BooleanField(default=False, verbose_name='保密台账')
    secret_category = models.CharField(max_length=64, blank=True, verbose_name='台账分类')
    
    qrcode = models.ImageField(upload_to='qrcodes/', blank=True, verbose_name='二维码')
    photo = models.ImageField(upload_to='device_photos/', blank=True, verbose_name='设备照片')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_devices', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'devices'
        verbose_name = '设备'
        verbose_name_plural = '设备'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.asset_no} - {self.name}"

    def save(self, *args, **kwargs):
        if self.workstation_id:
            self.location = self.workstation.location
            parts = []
            loc = self.location
            while loc:
                parts.insert(0, loc.name)
                loc = loc.parent
            parts.append(self.workstation.workstation_code)
            self.location_text = '-'.join(parts)
        elif self.location_id:
            parts = []
            loc = self.location
            while loc:
                parts.insert(0, loc.name)
                loc = loc.parent
            self.location_text = '-'.join(parts)
        super().save(*args, **kwargs)


class Workstation(models.Model):
    STATUS_CHOICES = [
        ('available', '可用'),
        ('occupied', '已占用'),
        ('maintenance', '维修中'),
    ]
    
    location = models.ForeignKey(AssetLocation, on_delete=models.CASCADE, related_name='workstations', verbose_name='所属位置')
    workstation_code = models.CharField(max_length=10, unique=True, verbose_name='工位编号')
    name = models.CharField(max_length=64, verbose_name='工位名称')
    x = models.FloatField(default=0, verbose_name='地图X坐标')
    y = models.FloatField(default=0, verbose_name='地图Y坐标')
    width = models.FloatField(default=30, verbose_name='工位宽度')
    height = models.FloatField(default=20, verbose_name='工位高度')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'workstations'
        verbose_name = '工位'
        verbose_name_plural = '工位'
        ordering = ['workstation_code']

    def __str__(self):
        return f"{self.workstation_code} - {self.name}"


class MapElement(models.Model):
    ELEMENT_TYPES = [
        ('wall', '墙'),
        ('door', '门'),
        ('window', '窗'),
        ('desk', '工位'),
        ('equipment', '设备'),
    ]
    DOOR_DIRECTIONS = [
        ('right', '右开'),
        ('left', '左开'),
        ('sliding', '推拉'),
    ]
    
    location = models.ForeignKey(AssetLocation, on_delete=models.CASCADE, related_name='map_elements', verbose_name='所属位置')
    element_type = models.CharField(max_length=20, choices=ELEMENT_TYPES, verbose_name='元素类型')
    x = models.FloatField(verbose_name='起点X坐标')
    y = models.FloatField(verbose_name='起点Y坐标')
    x2 = models.FloatField(null=True, blank=True, verbose_name='终点X坐标')
    y2 = models.FloatField(null=True, blank=True, verbose_name='终点Y坐标')
    width = models.FloatField(default=0, verbose_name='宽度')
    height = models.FloatField(default=0, verbose_name='高度')
    rotation = models.FloatField(default=0, verbose_name='旋转角度')
    color = models.CharField(max_length=7, default='#000000', verbose_name='颜色')
    thickness = models.IntegerField(default=2, verbose_name='线条粗细')
    points = models.TextField(blank=True, verbose_name='自定义点集')
    properties = models.TextField(blank=True, verbose_name='其他属性')
    sort_order = models.IntegerField(default=0, verbose_name='渲染顺序')
    door_direction = models.CharField(max_length=10, choices=DOOR_DIRECTIONS, default='right', verbose_name='门开方向')
    door_width = models.FloatField(default=60, verbose_name='门宽')
    door_open_angle = models.IntegerField(default=90, verbose_name='门打开角度')
    doorstop_width = models.FloatField(default=15, verbose_name='门垛宽度')
    auto_doorstop = models.BooleanField(default=True, verbose_name='自动生成门垛')
    snap_enabled = models.BooleanField(default=True, verbose_name='启用吸附')
    snap_threshold = models.FloatField(default=10, verbose_name='吸附阈值')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'map_elements'
        verbose_name = '地图元素'
        verbose_name_plural = '地图元素'
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.location.name} - {self.element_type}"


class MapBackground(models.Model):
    BG_TYPES = [
        ('image', '图片'),
        ('cad', 'CAD'),
        ('svg', 'SVG'),
    ]
    
    location = models.OneToOneField(AssetLocation, on_delete=models.CASCADE, related_name='background', verbose_name='所属位置')
    bg_type = models.CharField(max_length=20, choices=BG_TYPES, default='image', verbose_name='类型')
    file_path = models.CharField(max_length=256, blank=True, verbose_name='文件路径')
    file_data = models.BinaryField(null=True, blank=True, verbose_name='文件数据')
    scale = models.FloatField(default=1.0, verbose_name='缩放比例')
    offset_x = models.FloatField(default=0, verbose_name='X偏移')
    offset_y = models.FloatField(default=0, verbose_name='Y偏移')
    opacity = models.FloatField(default=1.0, verbose_name='透明度')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'map_backgrounds'
        verbose_name = '地图底图'
        verbose_name_plural = '地图底图'

    def __str__(self):
        return self.location.name


class SoftwareCategory(models.Model):
    name = models.CharField(max_length=64, verbose_name='分类名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级分类')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'software_categories'
        verbose_name = '软件分类'
        verbose_name_plural = '软件分类'

    def __str__(self):
        return self.name


class Software(models.Model):
    LICENSE_TYPES = [
        ('perpetual', '永久授权'),
        ('subscription', '订阅'),
        ('free', '免费'),
        ('trial', '试用'),
    ]
    
    name = models.CharField(max_length=128, verbose_name='软件名称')
    category = models.ForeignKey(SoftwareCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='software', verbose_name='分类')
    version = models.CharField(max_length=32, blank=True, verbose_name='版本')
    vendor = models.CharField(max_length=128, blank=True, verbose_name='供应商')
    license_type = models.CharField(max_length=32, choices=LICENSE_TYPES, default='perpetual', verbose_name='授权类型')
    license_count = models.IntegerField(null=True, blank=True, verbose_name='授权数量')
    license_used = models.IntegerField(default=0, verbose_name='已使用数量')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='购买日期')
    expire_date = models.DateField(null=True, blank=True, verbose_name='到期日期')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='价格')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'software'
        verbose_name = '软件资产'
        verbose_name_plural = '软件资产'

    def __str__(self):
        return self.name


class SoftwareLicense(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='licenses', verbose_name='软件')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='software_licenses', verbose_name='设备')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='software_licenses', verbose_name='使用人')
    license_key = models.CharField(max_length=256, blank=True, verbose_name='授权密钥')
    install_count = models.IntegerField(default=1, verbose_name='已安装次数')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')

    class Meta:
        db_table = 'software_licenses'
        verbose_name = '软件授权'
        verbose_name_plural = '软件授权'

    def __str__(self):
        return f"{self.software.name} - {self.user}"


class ConsumableCategory(models.Model):
    name = models.CharField(max_length=64, verbose_name='分类名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='上级分类')
    description = models.TextField(blank=True, verbose_name='描述')

    class Meta:
        db_table = 'consumable_categories'
        verbose_name = '耗材分类'
        verbose_name_plural = '耗材分类'

    def __str__(self):
        return self.name


class Consumable(models.Model):
    name = models.CharField(max_length=128, verbose_name='耗材名称')
    category = models.ForeignKey(ConsumableCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='consumables', verbose_name='分类')
    code = models.CharField(max_length=32, blank=True, verbose_name='耗材编码')
    specification = models.CharField(max_length=128, blank=True, verbose_name='规格型号')
    unit = models.CharField(max_length=16, default='个', verbose_name='单位')
    stock_quantity = models.IntegerField(default=0, verbose_name='库存数量')
    min_stock = models.IntegerField(default=0, verbose_name='最低库存预警')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='单价')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'consumables'
        verbose_name = '耗材物资'
        verbose_name_plural = '耗材物资'

    def __str__(self):
        return self.name


class ConsumableRecord(models.Model):
    RECORD_TYPES = [
        ('receive', '入库'),
        ('领用', '领用'),
        ('return', '归还'),
    ]
    
    consumable = models.ForeignKey(Consumable, on_delete=models.CASCADE, related_name='records', verbose_name='耗材')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='consumable_records', verbose_name='领用人')
    department = models.ForeignKey('accounts.Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='部门')
    quantity = models.IntegerField(verbose_name='数量')
    record_type = models.CharField(max_length=16, choices=RECORD_TYPES, verbose_name='记录类型')
    purpose = models.CharField(max_length=256, blank=True, verbose_name='用途')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_consumables', verbose_name='审批人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'consumable_records'
        verbose_name = '耗材记录'
        verbose_name_plural = '耗材记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.consumable.name} - {self.record_type}"


class ServiceType(models.Model):
    name = models.CharField(max_length=64, verbose_name='服务类型')
    description = models.TextField(blank=True, verbose_name='描述')
    sla_hours = models.IntegerField(default=24, verbose_name='SLA响应时限(小时)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'service_types'
        verbose_name = '服务类型'
        verbose_name_plural = '服务类型'

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('solved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    request_no = models.CharField(max_length=32, unique=True, verbose_name='请求编号')
    title = models.CharField(max_length=256, verbose_name='标题')
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests', verbose_name='服务类型')
    description = models.TextField(verbose_name='描述')
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests', verbose_name='请求人')
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests', verbose_name='处理人')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests', verbose_name='关联设备')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='截止时间')
    solved_at = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    rating = models.IntegerField(null=True, blank=True, verbose_name='评价评分')
    feedback = models.TextField(blank=True, verbose_name='评价反馈')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'service_requests'
        verbose_name = '服务请求'
        verbose_name_plural = '服务请求'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_no} - {self.title}"


class ServiceLog(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='logs', verbose_name='服务请求')
    handler = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='处理人')
    action = models.CharField(max_length=64, verbose_name='处理动作')
    content = models.TextField(verbose_name='处理内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'service_logs'
        verbose_name = '服务处理记录'
        verbose_name_plural = '服务处理记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request.request_no} - {self.action}"


class AssetLog(models.Model):
    ACTIONS = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('assign', '分配'),
        ('transfer', '转移'),
        ('repair', '维修'),
        ('scrap', '报废'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='logs', verbose_name='设备')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    action = models.CharField(max_length=20, choices=ACTIONS, verbose_name='操作')
    field_name = models.CharField(max_length=64, blank=True, verbose_name='变动字段')
    old_value = models.TextField(blank=True, verbose_name='旧值')
    new_value = models.TextField(blank=True, verbose_name='新值')
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'asset_logs'
        verbose_name = '资产日志'
        verbose_name_plural = '资产日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device.asset_no} - {self.action}"
