from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app import db

class AssetCategory(db.Model):
    """资产分类模型"""
    __tablename__ = 'asset_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, index=True)  # 分类名称
    level = db.Column(db.Integer, default=1)  # 分类级别 1-4
    parent_id = db.Column(db.Integer, db.ForeignKey('asset_categories.id'), nullable=True)  # 父分类ID
    code = db.Column(db.String(20), nullable=False, index=True)  # 分类编码
    description = db.Column(db.Text)  # 描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('AssetCategory', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    devices = db.relationship('Device', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<AssetCategory {self.name}>'

class Device(db.Model):
    """设备模型"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('asset_categories.id'), nullable=False)  # 分类ID
    asset_number = db.Column(db.String(64), nullable=False, unique=True, index=True)  # 资产编号
    device_number = db.Column(db.String(64), index=True)  # 设备编号
    name = db.Column(db.String(128))  # 名称
    model = db.Column(db.String(128))  # 型号
    serial_number = db.Column(db.String(128))  # 序列号
    status = db.Column(db.String(20), default='正常')  # 设备状态
    security_level = db.Column(db.String(20))  # 密级
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 用户ID
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))  # 部门ID
    location_id = db.Column(db.Integer, db.ForeignKey('asset_locations.id'))  # 位置ID
    purchase_date = db.Column(db.Date)  # 购入日期
    activation_date = db.Column(db.Date)  # 启用时间
    mac_address = db.Column(db.String(20))  # MAC地址
    ip_address = db.Column(db.String(20))  # IP地址
    operating_system = db.Column(db.String(64))  # 操作系统
    installation_date = db.Column(db.Date)  # 安装时间
    disk_serial = db.Column(db.String(128))  # 硬盘序列号
    purpose = db.Column(db.Text)  # 用途
    remarks = db.Column(db.Text)  # 备注
    is_fixed_asset = db.Column(db.Boolean, default=False)  # 固资在账
    card_number = db.Column(db.String(64))  # 卡片编号
    secret_inventory = db.Column(db.Boolean, default=False)  # 保密台账
    inventory_category = db.Column(db.String(64))  # 台账分类
    qr_code = db.Column(db.String(256))  # 二维码
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    category = db.relationship('AssetCategory', back_populates='devices')
    user = db.relationship('User', backref=db.backref('devices', lazy='dynamic'))
    department = db.relationship('Department', backref=db.backref('devices', lazy='dynamic'))
    location = db.relationship('AssetLocation', back_populates='devices')
    
    def __repr__(self):
        return f'<Device {self.name} ({self.asset_number})>'

class AssetLocation(db.Model):
    """资产位置模型"""
    __tablename__ = 'asset_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 位置名称
    level = db.Column(db.Integer, default=1)  # 位置级别 1-5 (1:园区, 2:建筑, 3:楼层, 4:子建筑, 5:具体位置)
    type = db.Column(db.String(20), default='location')  # 类型: park(园区), building(建筑), floor(楼层), sub_building(子建筑), location(具体位置)
    parent_id = db.Column(db.Integer, db.ForeignKey('asset_locations.id'), nullable=True)  # 父位置ID
    code = db.Column(db.String(20), nullable=False)  # 位置编码
    description = db.Column(db.Text)  # 描述
    map_data = db.Column(db.Text)  # 地图数据(SVG/Canvas绘制数据-JSON格式)
    
    # 坐标和尺寸属性
    coordinate_x = db.Column(db.Float)  # X坐标
    coordinate_y = db.Column(db.Float)  # Y坐标
    width = db.Column(db.Float)  # 宽度
    height = db.Column(db.Float)  # 高度
    
    # 建筑物特有属性
    is_multi_floor = db.Column(db.Boolean, default=False)  # 是否多层建筑
    floor_count = db.Column(db.Integer, default=1)  # 楼层数
    floor_names = db.Column(db.Text)  # 楼层名称(JSON数组)
    
    # 位置排序
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    parent = db.relationship('AssetLocation', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    devices = db.relationship('Device', back_populates='location', lazy='dynamic')
    
    def __repr__(self):
        return f'<AssetLocation {self.name} ({self.type})>'
    
    @property
    def path(self):
        """返回完整的位置路径字符串"""
        path_parts = []
        current = self
        
        # 递归获取所有父级位置名称
        while current:
            path_parts.insert(0, current.name)
            current = current.parent
            
        return '-'.join(path_parts)

class DeviceField(db.Model):
    """设备字段自定义模型"""
    __tablename__ = 'device_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # 字段名称
    field_key = db.Column(db.String(64), nullable=False, unique=True)  # 字段键名
    field_type = db.Column(db.String(20), default='text')  # 字段类型(text, select, date等)
    is_required = db.Column(db.Boolean, default=False)  # 是否必填
    is_visible = db.Column(db.Boolean, default=True)  # 是否可见
    options = db.Column(db.Text)  # 下拉选项(JSON)
    sort_order = db.Column(db.Integer, default=0)  # 排序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DeviceField {self.name}>'

class DeviceFieldValue(db.Model):
    """设备自定义字段值模型"""
    __tablename__ = 'device_field_values'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)  # 设备ID
    field_key = db.Column(db.String(64), nullable=False)  # 字段键名
    value = db.Column(db.Text)  # 值
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    device = db.relationship('Device', backref=db.backref('field_values', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('device_id', 'field_key', name='uix_device_field'),
    )
    
    def __repr__(self):
        return f'<DeviceFieldValue {self.field_key}={self.value}>' 