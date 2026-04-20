import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Department, Role, Permission
from apps.assets.models import (
    AssetCategory, AssetLocation, ServiceType, DeviceField, SoftwareField,
    Workstation, MapElement, MapBackground, LocationAreaBinding,
    Software, SoftwareCategory, SoftwareLicense,
    Consumable, ConsumableCategory, ConsumableRecord,
    AssetLog, LabelTemplate, ServiceContract
)
from apps.inventory.models import InventoryPlan, InventoryTask, InventoryRecord
from apps.todos.models import Todo, Notification
from apps.accounts.models import LoginLog
from apps.settings.models import SystemConfig, Organization


def init_permissions():
    """初始化权限数据，按侧边栏顺序排列：
    首页 -> 待办事项 -> 资产管理 -> 盘点管理 -> 组织管理 -> 工单服务 -> 日志管理 -> 系统设置
    """
    print("初始化权限...")
    
    permission_data = [
        # ==================== 1. 首页 (module=首页) ====================
        {'name': '首页', 'code': 'dashboard', 'type': 'menu', 'module': '首页', 'sort': 100},
        
        # ==================== 2. 待办事项 (module=待办, sort=200-299) ====================
        {'name': '待办事项', 'code': 'todo_module', 'type': 'menu', 'module': '待办', 'sort': 200},
        {'name': '我的待办', 'code': 'todo_list', 'type': 'menu', 'module': '待办', 'parent_code': 'todo_module', 'sort': 201},
        {'name': '待办创建', 'code': 'todo_create', 'type': 'button', 'module': '待办', 'parent_code': 'todo_list', 'sort': 202},
        {'name': '待办编辑', 'code': 'todo_edit', 'type': 'button', 'module': '待办', 'parent_code': 'todo_list', 'sort': 203},
        {'name': '待办删除', 'code': 'todo_delete', 'type': 'button', 'module': '待办', 'parent_code': 'todo_list', 'sort': 204},
        {'name': '通知消息', 'code': 'notification_list', 'type': 'menu', 'module': '待办', 'parent_code': 'todo_module', 'sort': 210},
        {'name': '通知删除', 'code': 'notification_delete', 'type': 'button', 'module': '待办', 'parent_code': 'notification_list', 'sort': 211},
        
        # ==================== 3. 资产管理 (module=资产, sort=300-399) ====================
        {'name': '资产管理', 'code': 'asset', 'type': 'menu', 'module': '资产', 'sort': 300},
        
        # 设备管理 (sort=301-319)
        {'name': '设备管理', 'code': 'device', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 301},
        {'name': '设备新增', 'code': 'device_create', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 302},
        {'name': '设备编辑', 'code': 'device_edit', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 303},
        {'name': '设备删除', 'code': 'device_delete', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 304},
        {'name': '设备查看', 'code': 'device_view', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 305},
        {'name': '设备导入', 'code': 'device_import', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 306},
        {'name': '设备导出', 'code': 'device_export', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 307},
        {'name': '报障', 'code': 'device_fault', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 308},
        {'name': '维修', 'code': 'device_repair', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 309},
        {'name': '报废', 'code': 'device_scrap', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 310},
        {'name': '批量报废', 'code': 'device_batch_scrap', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 311},
        {'name': '撤回', 'code': 'device_recall', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 312},
        {'name': '打印标签', 'code': 'device_print', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 313},
        {'name': '分配', 'code': 'device_assign', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 314},
        {'name': '回收', 'code': 'device_revoke', 'type': 'button', 'module': '资产', 'parent_code': 'device', 'sort': 315},
        {'name': '故障设备', 'code': 'device_fault_list', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 316},
        {'name': '报废设备', 'code': 'device_scrap_list', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 317},
        
        # 软件管理 (sort=320-329)
        {'name': '软件管理', 'code': 'software', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 320},
        {'name': '软件新增', 'code': 'software_create', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 321},
        {'name': '软件编辑', 'code': 'software_edit', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 322},
        {'name': '软件删除', 'code': 'software_delete', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 323},
        {'name': '软件查看', 'code': 'software_view', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 324},
        {'name': '软件导入', 'code': 'software_import', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 325},
        {'name': '软件导出', 'code': 'software_export', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 326},
        {'name': '授权分配', 'code': 'software_license', 'type': 'button', 'module': '资产', 'parent_code': 'software', 'sort': 327},
        
        # 服务管理 (sort=330-339)
        {'name': '服务管理', 'code': 'service_contract', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 330},
        {'name': '服务新增', 'code': 'service_contract_create', 'type': 'button', 'module': '资产', 'parent_code': 'service_contract', 'sort': 331},
        {'name': '服务编辑', 'code': 'service_contract_edit', 'type': 'button', 'module': '资产', 'parent_code': 'service_contract', 'sort': 332},
        {'name': '服务删除', 'code': 'service_contract_delete', 'type': 'button', 'module': '资产', 'parent_code': 'service_contract', 'sort': 333},
        {'name': '服务查看', 'code': 'service_contract_view', 'type': 'button', 'module': '资产', 'parent_code': 'service_contract', 'sort': 334},
        
        # 耗材管理 (sort=340-349)
        {'name': '耗材管理', 'code': 'consumable', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 340},
        {'name': '耗材新增', 'code': 'consumable_create', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 341},
        {'name': '耗材编辑', 'code': 'consumable_edit', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 342},
        {'name': '耗材删除', 'code': 'consumable_delete', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 343},
        {'name': '耗材查看', 'code': 'consumable_view', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 344},
        {'name': '耗材入库', 'code': 'consumable_receive', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 345},
        {'name': '耗材领用', 'code': 'consumable_use', 'type': 'button', 'module': '资产', 'parent_code': 'consumable', 'sort': 346},
        
        # 分类管理 (sort=350-359)
        {'name': '分类管理', 'code': 'category', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 350},
        {'name': '分类新增', 'code': 'category_create', 'type': 'button', 'module': '资产', 'parent_code': 'category', 'sort': 351},
        {'name': '分类编辑', 'code': 'category_edit', 'type': 'button', 'module': '资产', 'parent_code': 'category', 'sort': 352},
        {'name': '分类删除', 'code': 'category_delete', 'type': 'button', 'module': '资产', 'parent_code': 'category', 'sort': 353},
        
        # 位置管理 (sort=360-369)
        {'name': '位置管理', 'code': 'location', 'type': 'menu', 'module': '资产', 'parent_code': 'asset', 'sort': 360},
        {'name': '位置新增', 'code': 'location_create', 'type': 'button', 'module': '资产', 'parent_code': 'location', 'sort': 361},
        {'name': '位置编辑', 'code': 'location_edit', 'type': 'button', 'module': '资产', 'parent_code': 'location', 'sort': 362},
        {'name': '位置删除', 'code': 'location_delete', 'type': 'button', 'module': '资产', 'parent_code': 'location', 'sort': 363},
        {'name': '地图编辑', 'code': 'location_map', 'type': 'button', 'module': '资产', 'parent_code': 'location', 'sort': 364},
        {'name': '工位管理', 'code': 'workstation_manage', 'type': 'button', 'module': '资产', 'parent_code': 'location', 'sort': 365},
        
        # ==================== 4. 盘点管理 (module=盘点, sort=400-499) ====================
        {'name': '盘点管理', 'code': 'inventory', 'type': 'menu', 'module': '盘点', 'sort': 400},
        {'name': '盘点任务', 'code': 'inventory_task', 'type': 'menu', 'module': '盘点', 'parent_code': 'inventory', 'sort': 410},
        {'name': '任务创建', 'code': 'inventory_task_create', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_task', 'sort': 411},
        {'name': '任务编辑', 'code': 'inventory_task_edit', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_task', 'sort': 412},
        {'name': '任务删除', 'code': 'inventory_task_delete', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_task', 'sort': 413},
        {'name': '任务查看', 'code': 'inventory_task_view', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_task', 'sort': 414},
        {'name': '盘点执行', 'code': 'inventory_execute', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_task', 'sort': 415},
        {'name': '盘点报表', 'code': 'inventory_report', 'type': 'menu', 'module': '盘点', 'parent_code': 'inventory', 'sort': 420},
        {'name': '报表导出', 'code': 'inventory_report_export', 'type': 'button', 'module': '盘点', 'parent_code': 'inventory_report', 'sort': 421},
        
        # ==================== 5. 组织管理 (module=组织, sort=500-599) ====================
        {'name': '组织管理', 'code': 'organization', 'type': 'menu', 'module': '组织', 'sort': 500},
        
        # 用户管理 (sort=510-519)
        {'name': '用户管理', 'code': 'user', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 510},
        {'name': '用户新增', 'code': 'user_create', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 511},
        {'name': '用户编辑', 'code': 'user_edit', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 512},
        {'name': '用户删除', 'code': 'user_delete', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 513},
        {'name': '用户查看', 'code': 'user_view', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 514},
        {'name': '用户导入', 'code': 'user_import', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 515},
        {'name': '用户导出', 'code': 'user_export', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 516},
        {'name': '重置密码', 'code': 'user_reset_password', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 517},
        {'name': '批量启用', 'code': 'user_batch_enable', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 518},
        {'name': '批量禁用', 'code': 'user_batch_disable', 'type': 'button', 'module': '组织', 'parent_code': 'user', 'sort': 519},
        
        # 部门管理 (sort=520-529)
        {'name': '部门管理', 'code': 'department', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 520},
        {'name': '部门新增', 'code': 'department_create', 'type': 'button', 'module': '组织', 'parent_code': 'department', 'sort': 521},
        {'name': '部门编辑', 'code': 'department_edit', 'type': 'button', 'module': '组织', 'parent_code': 'department', 'sort': 522},
        {'name': '部门删除', 'code': 'department_delete', 'type': 'button', 'module': '组织', 'parent_code': 'department', 'sort': 523},
        
        # 角色管理 (sort=530-539)
        {'name': '角色管理', 'code': 'role', 'type': 'menu', 'module': '组织', 'parent_code': 'organization', 'sort': 530},
        {'name': '角色新增', 'code': 'role_create', 'type': 'button', 'module': '组织', 'parent_code': 'role', 'sort': 531},
        {'name': '角色编辑', 'code': 'role_edit', 'type': 'button', 'module': '组织', 'parent_code': 'role', 'sort': 532},
        {'name': '角色删除', 'code': 'role_delete', 'type': 'button', 'module': '组织', 'parent_code': 'role', 'sort': 533},
        {'name': '角色查看', 'code': 'role_view', 'type': 'button', 'module': '组织', 'parent_code': 'role', 'sort': 534},
        
        # ==================== 6. 工单服务 (module=工单, sort=600-699) ====================
        {'name': '工单服务', 'code': 'workorder', 'type': 'menu', 'module': '工单', 'sort': 600},
        {'name': '服务请求', 'code': 'service_list', 'type': 'menu', 'module': '工单', 'parent_code': 'workorder', 'sort': 610},
        {'name': '创建工单', 'code': 'service_create', 'type': 'button', 'module': '工单', 'parent_code': 'service_list', 'sort': 611},
        {'name': '工单编辑', 'code': 'service_edit', 'type': 'button', 'module': '工单', 'parent_code': 'service_list', 'sort': 612},
        {'name': '工单删除', 'code': 'service_delete', 'type': 'button', 'module': '工单', 'parent_code': 'service_list', 'sort': 613},
        {'name': '工单查看', 'code': 'service_view', 'type': 'button', 'module': '工单', 'parent_code': 'service_list', 'sort': 614},
        {'name': '工单处理', 'code': 'service_process', 'type': 'button', 'module': '工单', 'parent_code': 'service_list', 'sort': 615},
        
        # ==================== 7. 日志管理 (module=日志, sort=700-799) ====================
        {'name': '日志管理', 'code': 'log', 'type': 'menu', 'module': '日志', 'sort': 700},
        {'name': '登录日志', 'code': 'login_log', 'type': 'menu', 'module': '日志', 'parent_code': 'log', 'sort': 710},
        {'name': '操作日志', 'code': 'operation_log', 'type': 'menu', 'module': '日志', 'parent_code': 'log', 'sort': 720},
        {'name': '资产日志', 'code': 'asset_log', 'type': 'menu', 'module': '日志', 'parent_code': 'log', 'sort': 730},
        
        # ==================== 8. 系统设置 (module=设置, sort=800-899) ====================
        {'name': '系统设置', 'code': 'settings', 'type': 'menu', 'module': '设置', 'sort': 800},
        {'name': '系统配置', 'code': 'config', 'type': 'menu', 'module': '设置', 'parent_code': 'settings', 'sort': 810},
        {'name': '配置编辑', 'code': 'config_edit', 'type': 'button', 'module': '设置', 'parent_code': 'config', 'sort': 811},
        {'name': '企业信息', 'code': 'org_info', 'type': 'menu', 'module': '设置', 'parent_code': 'settings', 'sort': 820},
        {'name': '企业编辑', 'code': 'org_edit', 'type': 'button', 'module': '设置', 'parent_code': 'org_info', 'sort': 821},
        {'name': '数据管理', 'code': 'data_management', 'type': 'menu', 'module': '设置', 'parent_code': 'settings', 'sort': 830},
        {'name': '数据备份', 'code': 'data_backup', 'type': 'button', 'module': '设置', 'parent_code': 'data_management', 'sort': 831},
        {'name': '数据恢复', 'code': 'data_restore', 'type': 'button', 'module': '设置', 'parent_code': 'data_management', 'sort': 832},
        {'name': '数据清理', 'code': 'data_cleanup', 'type': 'button', 'module': '设置', 'parent_code': 'data_management', 'sort': 833},
        {'name': '个人设置', 'code': 'profile', 'type': 'menu', 'module': '设置', 'parent_code': 'settings', 'sort': 840},
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
    
    # 超级管理员 - 所有权限
    admin_role, _ = Role.objects.get_or_create(
        code='admin',
        defaults={
            'name': '超级管理员',
            'description': '拥有系统所有权限',
            'sort': 1,
        }
    )
    admin_role.permissions.set(permissions)
    
    # 普通用户 - 基本查看和待办权限
    user_role, _ = Role.objects.get_or_create(
        code='user',
        defaults={
            'name': '普通用户',
            'description': '普通用户基本权限',
            'sort': 2,
        }
    )
    user_basic_perms = Permission.objects.filter(code__in=[
        # 待办事项 - 我的待办
        'todo_create', 'todo_edit', 'todo_delete', 'todo_complete',
        # 待办事项 - 通知消息
        'notification_read', 'notification_mark_all_read', 'notification_delete',
        # 资产管理 - 查看权限
        'device_view', 'software_view', 'service_contract_view', 'consumable_view',
        # 盘点管理 - 查看权限
        'inventory_task_view',
        # 工单服务 - 创建和查看
        'service_create', 'service_view',
        # 日志 - 查看权限
        'login_log_view', 'operation_log_view', 'asset_log_view',
        # 个人设置
        'profile_edit',
    ])
    user_role.permissions.set(user_basic_perms)
    
    return admin_role


def init_departments():
    print("初始化部门...")
    depts = [
        {'name': '总经办', 'code': 'GMO', 'sort': 0},
        {'name': '财务部', 'code': 'FIN', 'sort': 1},
        {'name': '采购部', 'code': 'PUR', 'sort': 2},
        {'name': '市场部', 'code': 'MKT', 'sort': 3},
        {'name': '行政部', 'code': 'ADM', 'sort': 4},
        {'name': '质量部', 'code': 'QA', 'sort': 5},
        {'name': '审计部', 'code': 'AUD', 'sort': 6},
        {'name': '人力资源部', 'code': 'HR', 'sort': 7},
        {'name': '经营管理部', 'code': 'BMD', 'sort': 8},
        {'name': '仓储物流部', 'code': 'LOG', 'sort': 9},
        {'name': '研发设计部', 'code': 'RDE', 'sort': 10},
        {'name': '数控中心', 'code': 'CNC', 'sort': 11},
        {'name': '复材中心', 'code': 'CMC', 'sort': 12},
        {'name': '航材及装配中心', 'code': 'AMAC', 'sort': 13},
    ]
    
    for d in depts:
        Department.objects.get_or_create(code=d['code'], defaults=d)


def init_categories():
    print("初始化资产分类...")
    
    xcd, _ = AssetCategory.objects.get_or_create(
        code='XACD', defaults=dict(name='西安驰达', level=1, description='西安驰达飞机零部件制造股份有限公司', sort=1)
    )
    xays, _ = AssetCategory.objects.get_or_create(
        code='XAYS', defaults=dict(name='西安优盛', level=1, description='西安优盛航空科技有限公司', sort=2)
    )
    xabej, _ = AssetCategory.objects.get_or_create(
        code='XABEJ', defaults=dict(name='宝尔捷', level=1, description='', sort=80)
    )
    
    z_xcd, _ = AssetCategory.objects.get_or_create(
        code='Z', defaults=dict(name='总经办', parent=xcd, level=2, sort=1)
    )
    z_xays, _ = AssetCategory.objects.get_or_create(
        code='Z', defaults=dict(name='总经办', parent=xays, level=2, sort=1)
    )
    z_xabej, _ = AssetCategory.objects.get_or_create(
        code='Z', defaults=dict(name='总经办', parent=xabej, level=2, sort=1)
    )
    
    jsj_xcd, _ = AssetCategory.objects.get_or_create(
        code='001', parent=z_xcd, defaults=dict(name='计算机', level=3, sort=1)
    )
    bgs_xcd, _ = AssetCategory.objects.get_or_create(
        code='002', parent=z_xcd, defaults=dict(name='办公设备', level=3, sort=2)
    )
    xx_xcd, _ = AssetCategory.objects.get_or_create(
        code='003', parent=z_xcd, defaults=dict(name='信息设备', level=3, sort=3)
    )
    
    jsj_xays, _ = AssetCategory.objects.get_or_create(
        code='001', parent=z_xays, defaults=dict(name='计算机', level=3, sort=1)
    )
    bgs_xays, _ = AssetCategory.objects.get_or_create(
        code='002', parent=z_xays, defaults=dict(name='办公设备', level=3, sort=2)
    )
    xx_xays, _ = AssetCategory.objects.get_or_create(
        code='003', parent=z_xays, defaults=dict(name='信息设备', level=3, sort=3)
    )
    
    jsj_xabej, _ = AssetCategory.objects.get_or_create(
        code='001', parent=z_xabej, defaults=dict(name='计算机', level=3, sort=1)
    )
    bgs_xabej, _ = AssetCategory.objects.get_or_create(
        code='002', parent=z_xabej, defaults=dict(name='办公设备', level=3, sort=2)
    )
    xx_xabej, _ = AssetCategory.objects.get_or_create(
        code='003', parent=z_xabej, defaults=dict(name='信息设备', level=3, sort=3)
    )
    
    computer_children = [
        ('台式机', '001', 1), ('笔记本', '002', 2), ('显示器', '003', 3), ('其他', '004', 4)
    ]
    for name, code, sort in computer_children:
        AssetCategory.objects.get_or_create(
            code=code, parent=jsj_xcd, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=jsj_xays, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=jsj_xabej, defaults=dict(name=name, level=4, sort=sort)
        )
    
    office_children = [
        ('空调', '001', 1), ('打印机', '002', 2), ('扫描仪', '003', 3), ('传真机', '004', 4), 
        ('投影仪', '005', 5), ('交换机', '006', 6), ('平板一体机', '007', 7), ('照相机', '008', 8), ('其他', '009', 9)
    ]
    for name, code, sort in office_children:
        AssetCategory.objects.get_or_create(
            code=code, parent=bgs_xcd, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=bgs_xays, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=bgs_xabej, defaults=dict(name=name, level=4, sort=sort)
        )
    
    info_children = [
        ('服务器', '001', 1), ('存储器', '002', 2), ('监控设备', '003', 3), ('监控系统', '004', 4), ('其他', '005', 5)
    ]
    for name, code, sort in info_children:
        AssetCategory.objects.get_or_create(
            code=code, parent=xx_xcd, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=xx_xays, defaults=dict(name=name, level=4, sort=sort)
        )
        AssetCategory.objects.get_or_create(
            code=code, parent=xx_xabej, defaults=dict(name=name, level=4, sort=sort)
        )
    
    print(f"已初始化 {AssetCategory.objects.count()} 条分类数据")


def init_locations():
    print("初始化位置...")
    
    cy, _ = AssetLocation.objects.get_or_create(
        code='CY',
        defaults={'name': '产业园区', 'level': 1, 'park_code': 'CY', 'sort': 1}
    )
    
    oa, _ = AssetLocation.objects.get_or_create(
        code='CYOA',
        defaults={'name': '办公楼', 'level': 2, 'park_code': 'CY', 'building_code': 'OA', 'sort': 1}
    )
    oa.parent = cy
    oa.save()
    
    floors = [
        ('B1层', 'CYOAB1', 'B1', 0, True),
        ('1楼', 'CYOA01', '01', 0, True),
        ('2楼', 'CYOA02', '02', 0, True),
        ('3楼', 'CYOA03', '03', 0, True),
        ('4楼', 'CYOA04', '04', 0, True),
        ('5楼', 'CYOA05', '05', 0, True),
        ('天台', 'CYOAC1', 'C1', 7, False),
    ]
    
    floor_objs = {}
    for name, code, floor_code, sort, has_map in floors:
        floor, _ = AssetLocation.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'level': 3,
                'parent': oa,
                'park_code': 'CY',
                'building_code': 'OA',
                'floor_code': floor_code,
                'sort': sort,
                'has_map': has_map,
                'map_width': 1200,
                'map_height': 800,
                'grid_size': 30,
                'default_snap_threshold': 10,
                'default_snap_enabled': True,
            }
        )
        floor_objs[code] = floor
    
    rooms = [
        ('CYOA02-A201', '2楼', 'A201'),
        ('CYOA02-B1', '2楼', '办公区B1'),
    ]
    
    for parent_code, floor_name, room_name in rooms:
        parent = floor_objs.get(parent_code)
        if parent:
            AssetLocation.objects.get_or_create(
                code=f"{parent_code}-{room_name}",
                defaults={
                    'name': room_name,
                    'level': 4,
                    'parent': parent,
                    'park_code': parent_code,
                    'sort': 0
                }
            )
    
    print(f"已初始化 {AssetLocation.objects.count()} 条位置数据")


def init_service_types():
    print("初始化服务类型...")
    types = [
        {'name': '硬件故障', 'sla_hours': 24},
        {'name': '软件问题', 'sla_hours': 8},
        {'name': '网络故障', 'sla_hours': 4},
        {'name': '账号问题', 'sla_hours': 8},
        {'name': '维保服务', 'sla_hours': 24},
        {'name': '技术支持', 'sla_hours': 8},
        {'name': '售后服务', 'sla_hours': 12},
        {'name': '培训服务', 'sla_hours': 24},
        {'name': '咨询服务', 'sla_hours': 48},
    ]
    
    for t in types:
        ServiceType.objects.get_or_create(name=t['name'], defaults=t)


def init_system_config():
    print("初始化系统配置...")
    configs = [
        # 基础设置
        {'config_key': 'system_name', 'config_value': '驰达IT资产管理系统', 'config_group': 'basic', 'description': '系统名称', 'sort': 1},
        {'config_key': 'system_short_name', 'config_value': 'CDITAMS', 'value_type': 'string', 'config_group': 'basic', 'description': '系统简称', 'sort': 2},
        {'config_key': 'app_url', 'config_value': 'http://127.0.0.1:8000', 'config_group': 'basic', 'description': '应用URL（用于生成二维码等外部链接）', 'sort': 3},
        {'config_key': 'timezone', 'config_value': 'Asia/Shanghai', 'value_type': 'select', 'config_group': 'basic', 'description': '系统时区', 'sort': 4, 'options': '[["Asia/Shanghai", "Asia/Shanghai (UTC+8)"], ["UTC", "UTC (UTC+0)"], ["America/New_York", "America/New_York (UTC-5)"]]'},
        # 安全设置
        {'config_key': 'password_expire_days', 'config_value': '0', 'value_type': 'int', 'config_group': 'security', 'description': '密码过期天数（0表示永不过期）', 'sort': 1},
        {'config_key': 'login_lock_attempts', 'config_value': '0', 'value_type': 'int', 'config_group': 'security', 'description': '登录失败锁定次数（0表示不锁定）', 'sort': 2},
        {'config_key': 'session_timeout_minutes', 'config_value': '120', 'value_type': 'int', 'config_group': 'security', 'description': '会话超时时间（分钟）', 'sort': 3},
        # 资产设置
        {'config_key': 'asset_auto_number', 'config_value': 'true', 'value_type': 'boolean', 'config_group': 'asset', 'description': '资产自动编号开关', 'sort': 1},
        # 模型设置
        {'config_key': 'llm_enabled', 'config_value': 'false', 'value_type': 'boolean', 'config_group': 'model', 'description': '启用大语言模型', 'sort': 1},
        {'config_key': 'llm_api_base', 'config_value': 'https://api.xiaomimimo.com/v1', 'value_type': 'string', 'config_group': 'model', 'description': 'API 基础地址 (base_url)', 'sort': 2},
        {'config_key': 'llm_api_key', 'config_value': '', 'value_type': 'string', 'config_group': 'model', 'description': 'API Key', 'sort': 3},
        {'config_key': 'llm_model_name', 'config_value': 'mimo-v2-pro', 'value_type': 'string', 'config_group': 'model', 'description': '模型名称 (model)', 'sort': 4},
        {'config_key': 'llm_temperature', 'config_value': '1.0', 'value_type': 'string', 'config_group': 'model', 'description': '温度 (temperature) 取值范围 0~2', 'sort': 5},
        {'config_key': 'llm_top_p', 'config_value': '0.95', 'value_type': 'string', 'config_group': 'model', 'description': '核采样 (top_p) 取值范围 0~1', 'sort': 6},
        {'config_key': 'llm_max_tokens', 'config_value': '4096', 'value_type': 'int', 'config_group': 'model', 'description': '最大生成长度 (max_completion_tokens)', 'sort': 7},
        {'config_key': 'llm_frequency_penalty', 'config_value': '0', 'value_type': 'string', 'config_group': 'model', 'description': '频率惩罚 (frequency_penalty) 取值范围 -2~2', 'sort': 8},
        {'config_key': 'llm_presence_penalty', 'config_value': '0', 'value_type': 'string', 'config_group': 'model', 'description': '存在惩罚 (presence_penalty) 取值范围 -2~2', 'sort': 9},
        {'config_key': 'llm_stream', 'config_value': 'false', 'value_type': 'boolean', 'config_group': 'model', 'description': '流式输出 (stream)', 'sort': 10},
    ]
    
    for c in configs:
        SystemConfig.objects.update_or_create(config_key=c['config_key'], defaults=c)


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
        dept = Department.objects.filter(code='GMO').first()
        user = User.objects.create_user(
            username='86000001',
            emp_no='86000001',
            realname='管理员',
            password='password',
            is_superuser=True,
            is_staff=True,
            department=dept
        )
        role = Role.objects.first()
        if role:
            user.role = role
            user.save()
        print("超级管理员创建成功: 86000001 / password")


def init_device_fields():
    print("初始化设备系统字段...")
    
    system_fields = [
        {'name': '资产分类', 'field_key': 'category', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 1},
        {'name': '资产编号', 'field_key': 'asset_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 2},
        {'name': '设备编号', 'field_key': 'device_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 3},
        {'name': '设备名称', 'field_key': 'name', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 4},
        {'name': '型号', 'field_key': 'model', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 5},
        {'name': '序列号', 'field_key': 'serial_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': False, 'sort': 6},
        {'name': '密级', 'field_key': 'secret_level', 'field_type': 'select', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 7, 'options': '["public", "internal", "confidential", "secret", "top_secret", "commercial_secret"]'},
        {'name': '所属部门', 'field_key': 'department', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 8},
        {'name': '使用人', 'field_key': 'user', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 9},
        {'name': '位置', 'field_key': 'location', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 10},
        {'name': '工位', 'field_key': 'workstation', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': False, 'sort': 11},
        {'name': '设备状态', 'field_key': 'status', 'field_type': 'select', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 12, 'options': '["normal", "fault", "scrapped", "unused"]'},
        {'name': 'MAC地址', 'field_key': 'mac_address', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 13},
        {'name': 'IP地址', 'field_key': 'ip_address', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 14},
        {'name': '操作系统', 'field_key': 'os_name', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 15},
        {'name': '安装时间', 'field_key': 'install_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 16},
        {'name': '硬盘序列号', 'field_key': 'disk_serial', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 17},
        {'name': '购入日期', 'field_key': 'purchase_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 18},
        {'name': '启用时间', 'field_key': 'enable_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 19},
        {'name': '用途', 'field_key': 'purpose', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 20},
        {'name': '备注', 'field_key': 'remarks', 'field_type': 'textarea', 'is_system': True, 'is_visible': True, 'is_card_visible': False, 'sort': 21},
        {'name': '固资在账', 'field_key': 'is_fixed', 'field_type': 'checkbox', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 22},
        {'name': '卡片编号', 'field_key': 'asset_card_no', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 23},
        {'name': '保密台账', 'field_key': 'is_secret', 'field_type': 'checkbox', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 24},
        {'name': '台账分类', 'field_key': 'secret_category', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 25},
        {'name': '二维码', 'field_key': 'qrcode', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 26},
        {'name': '设备照片', 'field_key': 'photo', 'field_type': 'text', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 27},
        {'name': '创建时间', 'field_key': 'created_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 28},
        {'name': '更新时间', 'field_key': 'updated_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 29},
    ]
    
    for field_data in system_fields:
        field_key = field_data.pop('field_key')
        DeviceField.objects.update_or_create(
            field_key=field_key,
            defaults=field_data
        )
    print(f"已初始化 {len(system_fields)} 个设备系统字段")


def init_software_fields():
    print("初始化软件系统字段...")
    
    from apps.assets.models import SoftwareField
    
    system_fields = [
        {'name': '软件名称', 'field_key': 'name', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 1},
        {'name': '资产编号', 'field_key': 'asset_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 2},
        {'name': '编号', 'field_key': 'device_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 3},
        {'name': '版本', 'field_key': 'version', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 4},
        {'name': '供应商', 'field_key': 'vendor', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 5},
        {'name': '授权类型', 'field_key': 'license_type', 'field_type': 'select', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 6},
        {'name': '授权数量', 'field_key': 'license_count', 'field_type': 'number', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 7},
        {'name': '价格', 'field_key': 'price', 'field_type': 'number', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 8},
        {'name': '购买日期', 'field_key': 'purchase_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 9},
        {'name': '到期日期', 'field_key': 'expire_date', 'field_type': 'date', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 10},
        {'name': '固资在账', 'field_key': 'is_fixed', 'field_type': 'checkbox', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 11},
        {'name': '卡片编号', 'field_key': 'asset_card_no', 'field_type': 'text', 'is_system': True, 'is_visible': True, 'is_card_visible': True, 'sort': 12},
        {'name': '描述', 'field_key': 'description', 'field_type': 'textarea', 'is_system': True, 'is_visible': True, 'is_card_visible': False, 'sort': 13},
        {'name': '创建时间', 'field_key': 'created_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 14},
        {'name': '更新时间', 'field_key': 'updated_at', 'field_type': 'datetime', 'is_system': True, 'is_visible': False, 'is_card_visible': False, 'sort': 15},
    ]
    
    for field_data in system_fields:
        field_key = field_data.pop('field_key')
        SoftwareField.objects.update_or_create(
            field_key=field_key,
            defaults=field_data
        )
    print(f"已初始化 {len(system_fields)} 个软件系统字段")


def init_software_categories():
    print("初始化软件分类...")
    
    categories = [
        {'name': '操作系统', 'description': '操作系统类软件'},
        {'name': '办公软件', 'description': '办公自动化软件'},
        {'name': '开发工具', 'description': '软件开发工具'},
        {'name': '安全软件', 'description': '杀毒、防火墙等安全软件'},
        {'name': '设计软件', 'description': 'CAD、Photoshop等设计软件'},
        {'name': '行业软件', 'description': '专业行业软件'},
        {'name': '数据库', 'description': '数据库管理系统'},
        {'name': '中间件', 'description': '应用中间件'},
        {'name': '其他', 'description': '其他软件'},
    ]
    
    for cat_data in categories:
        SoftwareCategory.objects.get_or_create(name=cat_data['name'], defaults=cat_data)
    
    print(f"已初始化 {SoftwareCategory.objects.count()} 条软件分类数据")


def init_consumable_categories():
    print("初始化耗材分类...")
    
    categories = [
        {'name': '办公耗材', 'description': '纸张、笔等办公用品'},
        {'name': '打印耗材', 'description': '墨盒、硒鼓、碳粉等'},
        {'name': '电脑配件', 'description': '内存、硬盘、鼠标、键盘等'},
        {'name': '网络设备', 'description': '网线、水晶头、交换机配件等'},
        {'name': '存储介质', 'description': 'U盘、移动硬盘、光盘等'},
        {'name': '其他', 'description': '其他耗材物资'},
    ]
    
    for cat_data in categories:
        ConsumableCategory.objects.get_or_create(name=cat_data['name'], defaults=cat_data)
    
    print(f"已初始化 {ConsumableCategory.objects.count()} 条耗材分类数据")


def init_label_templates():
    print("初始化标签模板...")
    
    # 默认标签模板
    default_template, created = LabelTemplate.objects.get_or_create(
        is_default=True,
        defaults={
            'name': '默认标签模板',
            'size_type': '50x80',
            'width': 50,
            'height': 80,
            'fields_config': [
                {'field': 'asset_no', 'label': '资产编号', 'show': True},
                {'field': 'name', 'label': '设备名称', 'show': True},
                {'field': 'model', 'label': '型号', 'show': True},
                {'field': 'department', 'label': '部门', 'show': True},
                {'field': 'user', 'label': '使用人', 'show': True},
                {'field': 'location', 'label': '位置', 'show': True},
            ],
            'layout_config': {
                'font_size': 10,
                'show_qrcode': True,
                'qrcode_size': 25,
            }
        }
    )
    
    if created:
        print("已创建默认标签模板")
    else:
        print("默认标签模板已存在")


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
    init_software_fields()
    init_software_categories()
    init_consumable_categories()
    init_label_templates()
    create_superuser()
    
    print("数据初始化完成!")


if __name__ == '__main__':
    run()
