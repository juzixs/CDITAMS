import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Department, Role, Permission
from apps.assets.models import AssetCategory, AssetLocation, ServiceType, DeviceField
from apps.settings.models import SystemConfig, Organization

def init_permissions():
    print("初始化权限...")
    
    permission_data = [
        {'name': '首页', 'code': 'dashboard', 'type': 'menu', 'module': '首页', 'sort': 1},
        {'name': '资产管理', 'code': 'asset', 'type': 'menu', 'module': '资产', 'sort': 10},
        {'name': '设备管理', 'code': 'device', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 11},
        {'name': '设备新增', 'code': 'device_create', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 1},
        {'name': '设备编辑', 'code': 'device_edit', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 2},
        {'name': '设备删除', 'code': 'device_delete', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 3},
        {'name': '分类管理', 'code': 'category', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 12},
        {'name': '位置管理', 'code': 'location', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 13},
        {'name': '盘点管理', 'code': 'inventory', 'type': 'menu', 'module': '盘点', 'sort': 20},
        {'name': '盘点计划', 'code': 'plan', 'type': 'menu', 'module': '盘点', 'parent_code': 'inventory', 'sort': 21},
        {'name': '盘点任务', 'code': 'task', 'type': 'menu', 'module': '盘点', 'parent_code': 'inventory', 'sort': 22},
        {'name': '组织管理', 'code': 'organization', 'type': 'menu', 'module': '组织', 'sort': 30},
        {'name': '用户管理', 'code': 'user', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 31},
        {'name': '部门管理', 'code': 'department', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 32},
        {'name': '角色管理', 'code': 'role', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 33},
        {'name': '待办管理', 'code': 'todo', 'type': 'menu', 'module': '待办', 'sort': 40},
        {'name': '日志管理', 'code': 'log', 'type': 'menu', 'module': '日志', 'sort': 50},
        {'name': '系统设置', 'code': 'settings', 'type': 'menu', 'module': '设置', 'sort': 60},
    ]
    
    created = {}
    for data in permission_data:
        parent_code = data.pop('parent_code', None)
        perm, _ = Permission.objects.get_or_create(code=data['code'], defaults=data)
        if parent_code and parent_code in created:
            perm.parent = created[parent_code]
            perm.save()
        created[data['code']] = perm
    
    return created

def init_roles():
    print("初始化角色...")
    permissions = Permission.objects.all()
    
    role, _ = Role.objects.get_or_create(
        code='admin',
        defaults={
            'name': '超级管理员',
            'description': '拥有系统所有权限'
        }
    )
    role.permissions.set(permissions)
    return role

def init_departments():
    print("初始化部门...")
    depts = [
        {'name': '总经理办公室', 'code': 'OFFICE', 'sort': 1},
        {'name': '技术部', 'code': 'TECH', 'sort': 2},
        {'name': '财务部', 'code': 'FIN', 'sort': 3},
        {'name': '人力资源部', 'code': 'HR', 'sort': 4},
    ]
    
    for d in depts:
        Department.objects.get_or_create(code=d['code'], defaults=d)

def init_categories():
    print("初始化资产分类...")
    cats = [
        {'name': '台式机', 'code': 'DJ', 'sort': 1},
        {'name': '笔记本电脑', 'code': 'BJ', 'sort': 2},
        {'name': '服务器', 'code': 'FW', 'sort': 3},
        {'name': '打印机', 'code': 'DY', 'sort': 4},
        {'name': '网络设备', 'code': 'WL', 'sort': 5},
    ]
    
    for c in cats:
        AssetCategory.objects.get_or_create(code=c['code'], defaults=c)

def init_locations():
    print("初始化位置...")
    locs = [
        {'name': '产业园区', 'code': 'CY', 'level': 1, 'park_code': 'CY', 'sort': 1},
        {'name': '办公楼A栋', 'code': 'OA', 'level': 2, 'building_code': 'OA', 'sort': 1},
        {'name': '3楼', 'code': '03', 'level': 3, 'floor_code': '03', 'sort': 1},
    ]
    
    for l in locs:
        AssetLocation.objects.get_or_create(code=l['code'], defaults=l)

def init_service_types():
    print("初始化服务类型...")
    types = [
        {'name': '硬件故障', 'sla_hours': 24},
        {'name': '软件问题', 'sla_hours': 8},
        {'name': '网络故障', 'sla_hours': 4},
        {'name': '账号问题', 'sla_hours': 8},
    ]
    
    for t in types:
        ServiceType.objects.get_or_create(name=t['name'], defaults=t)

def init_system_config():
    print("初始化系统配置...")
    configs = [
        {'config_key': 'company_name', 'config_value': '驰达', 'config_group': 'basic', 'description': '企业名称'},
        {'config_key': 'items_per_page', 'config_value': '20', 'value_type': 'int', 'config_group': 'basic', 'description': '默认分页数'},
        {'config_key': 'asset_code_prefix', 'config_value': 'DJ', 'config_group': 'asset', 'description': '资产编号前缀'},
    ]
    
    for c in configs:
        SystemConfig.objects.get_or_create(config_key=c['config_key'], defaults=c)

def init_org():
    print("初始化企业信息...")
    Organization.objects.get_or_create(
        code='CHIDA',
        defaults={
            'name': '西安驰达',
            'short_name': '驰达',
            'description': '驰达IT资产管理系统'
        }
    )

def create_superuser():
    print("创建超级管理员...")
    User = get_user_model()
    if not User.objects.filter(emp_no='86000001').exists():
        user = User.objects.create_user(
            username='86000001',
            emp_no='86000001',
            realname='管理员',
            password='password',
            is_superuser=True,
            is_staff=True
        )
        role = Role.objects.first()
        if role:
            user.role = role
            user.save()
        print("超级管理员创建成功: 86000001 / password")

def init_device_fields():
    print("初始化设备系统字段...")
    
    system_fields = [
        {'name': '资产编号', 'field_key': 'asset_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 1},
        {'name': '设备编号', 'field_key': 'device_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 2},
        {'name': '序列号', 'field_key': 'serial_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 3},
        {'name': '设备名称', 'field_key': 'name', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 4},
        {'name': '型号', 'field_key': 'model', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 5},
        {'name': '品牌', 'field_key': 'brand', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 6},
        {'name': '设备状态', 'field_key': 'status', 'field_type': 'select', 'is_system': True, 'is_visible': True, 'sort': 7, 'options': '["normal", "fault", "repairing", "scrapped", "unused"]'},
        {'name': '密级', 'field_key': 'secret_level', 'field_type': 'select', 'is_system': True, 'is_visible': True, 'sort': 8, 'options': '["public", "internal", "confidential", "secret"]'},
        {'name': '使用人', 'field_key': 'user', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 9},
        {'name': '所属部门', 'field_key': 'department', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 10},
        {'name': '所在位置', 'field_key': 'location', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'sort': 11},
        {'name': 'MAC地址', 'field_key': 'mac_address', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 12},
        {'name': 'IP地址', 'field_key': 'ip_address', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 13},
        {'name': '操作系统', 'field_key': 'os_name', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 14},
        {'name': '系统版本', 'field_key': 'os_version', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 15},
        {'name': '硬盘序列号', 'field_key': 'disk_serial', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 16},
        {'name': '用途', 'field_key': 'purpose', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 17},
        {'name': '购入日期', 'field_key': 'purchase_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'sort': 18},
        {'name': '启用时间', 'field_key': 'enable_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'sort': 19},
        {'name': '安装时间', 'field_key': 'install_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'sort': 20},
        {'name': '固资在账', 'field_key': 'is_fixed', 'field_type': 'checkbox', 'is_system': True, 'is_visible': False, 'sort': 21},
        {'name': '卡片编号', 'field_key': 'asset_card_no', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 22},
        {'name': '保密台账', 'field_key': 'is_secret', 'field_type': 'checkbox', 'is_system': True, 'is_visible': False, 'sort': 23},
        {'name': '台账分类', 'field_key': 'secret_category', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'sort': 24},
        {'name': '备注', 'field_key': 'remarks', 'field_type': 'textarea', 'is_system': True, 'is_visible': False, 'sort': 25},
        {'name': '创建时间', 'field_key': 'created_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': True, 'sort': 26},
        {'name': '更新时间', 'field_key': 'updated_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': False, 'sort': 27},
    ]
    
    for field_data in system_fields:
        field_key = field_data.pop('field_key')
        DeviceField.objects.update_or_create(
            field_key=field_key,
            defaults=field_data
        )
    print(f"已初始化 {len(system_fields)} 个系统字段")

def run():
    print("开始初始化数据...")
    
    init_permissions()
    init_roles()
    init_departments()
    init_categories()
    init_locations()
    init_service_types()
    init_system_config()
    init_org()
    init_device_fields()
    create_superuser()
    
    print("数据初始化完成!")

if __name__ == '__main__':
    run()
