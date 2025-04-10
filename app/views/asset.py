from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import json
from datetime import datetime
from sqlalchemy import or_

from app import db
from app.models import Device, AssetCategory, AssetLocation, DeviceField

asset = Blueprint('asset', __name__)

# 设备列表页面
@asset.route('/devices')
@login_required
def device_list():
    return render_template('asset/device/list.html')

# 获取设备列表数据
@asset.route('/api/devices', methods=['GET'])
@login_required
def get_devices():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 10, type=int)
    search = request.args.get('search', '')
    
    query = Device.query
    
    # 搜索
    if search:
        query = query.filter(or_(
            Device.asset_number.contains(search),
            Device.device_number.contains(search),
            Device.name.contains(search),
            Device.model.contains(search),
            Device.serial_number.contains(search)
        ))
    
    # 分页
    pagination = query.order_by(Device.id.desc()).paginate(page=page, per_page=size)
    devices = pagination.items
    
    # 转换为dict
    devices_list = []
    for device in devices:
        device_dict = {
            'id': device.id,
            'category': device.category.name if device.category else '-',
            'asset_number': device.asset_number,
            'device_number': device.device_number or '-',
            'name': device.name or '-',
            'model': device.model or '-',
            'serial_number': device.serial_number or '-',
            'status': device.status or '-',
            'security_level': device.security_level or '-',
            'user': device.user.name if device.user else '-',
            'department': device.department.name if device.department else '-',
            'location': device.location.name if device.location else '-',
            'purchase_date': device.purchase_date.strftime('%Y-%m-%d') if device.purchase_date else '-',
            'activation_date': device.activation_date.strftime('%Y-%m-%d') if device.activation_date else '-',
            'mac_address': device.mac_address or '-',
            'ip_address': device.ip_address or '-',
            'operating_system': device.operating_system or '-',
            'installation_date': device.installation_date.strftime('%Y-%m-%d') if device.installation_date else '-',
            'disk_serial': device.disk_serial or '-',
            'purpose': device.purpose or '-',
            'remarks': device.remarks or '-',
            'is_fixed_asset': '是' if device.is_fixed_asset else '否',
            'card_number': device.card_number or '-',
            'secret_inventory': '是' if device.secret_inventory else '否',
            'inventory_category': device.inventory_category or '-',
            'qr_code': device.qr_code or '-'
        }
        devices_list.append(device_dict)
    
    return jsonify({
        'data': devices_list,
        'total': pagination.total,
        'page': pagination.page,
        'size': pagination.per_page,
        'pages': pagination.pages
    })

# 设备详情页面
@asset.route('/devices/<int:id>')
@login_required
def device_detail(id):
    device = Device.query.get_or_404(id)
    return render_template('asset/device/detail.html', device=device)

# 新增设备页面
@asset.route('/devices/create')
@login_required
def device_create():
    categories = AssetCategory.query.filter_by(level=1).all()
    return render_template('asset/device/form.html', categories=categories)

# 编辑设备页面
@asset.route('/devices/<int:id>/edit')
@login_required
def device_edit(id):
    device = Device.query.get_or_404(id)
    categories = AssetCategory.query.filter_by(level=1).all()
    return render_template('asset/device/form.html', device=device, categories=categories)

# 保存设备
@asset.route('/api/devices', methods=['POST'])
@login_required
def save_device():
    data = request.json
    
    device_id = data.get('id')
    if device_id:
        device = Device.query.get_or_404(device_id)
    else:
        device = Device()
    
    # 必填项检查
    if not data.get('category_id'):
        return jsonify({'success': False, 'message': '分类不能为空'}), 400
    
    if not data.get('asset_number'):
        return jsonify({'success': False, 'message': '资产编号不能为空'}), 400
    
    # 设置属性
    for key, value in data.items():
        if key != 'id' and hasattr(device, key):
            setattr(device, key, value)
    
    # 保存
    try:
        if not device_id:
            db.session.add(device)
        db.session.commit()
        return jsonify({'success': True, 'message': '保存成功', 'id': device.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 删除设备
@asset.route('/api/devices/<int:id>', methods=['DELETE'])
@login_required
def delete_device(id):
    device = Device.query.get_or_404(id)
    
    try:
        db.session.delete(device)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 批量删除设备
@asset.route('/api/devices/batch', methods=['DELETE'])
@login_required
def batch_delete_devices():
    ids = request.json.get('ids', [])
    
    if not ids:
        return jsonify({'success': False, 'message': '请选择要删除的设备'}), 400
    
    try:
        Device.query.filter(Device.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True, 'message': f'成功删除 {len(ids)} 台设备'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 生成资产编号
@asset.route('/api/devices/generate-asset-number', methods=['POST'])
@login_required
def generate_asset_number():
    category_id = request.json.get('category_id')
    
    if not category_id:
        return jsonify({'success': False, 'message': '请选择分类'}), 400
    
    try:
        # 获取分类信息
        category = AssetCategory.query.get_or_404(category_id)
        
        # 获取父级分类
        parent_codes = []
        current = category
        
        # 从当前分类回溯到顶级分类，收集所有编码
        while current:
            parent_codes.insert(0, current.code)
            if current.parent_id:
                current = AssetCategory.query.get(current.parent_id)
            else:
                break
        
        # 构建基础资产编号前缀
        asset_number_prefix = '-'.join(parent_codes)
        
        # 查找同前缀的最大编号
        max_device = Device.query.filter(
            Device.asset_number.like(f"{asset_number_prefix}-%")
        ).order_by(Device.asset_number.desc()).first()
        
        if max_device:
            # 提取最后一个序号并递增
            last_part = max_device.asset_number.split('-')[-1]
            try:
                new_seq = int(last_part) + 1
                new_seq_str = f"{new_seq:03d}"
            except ValueError:
                new_seq_str = "001"
        else:
            new_seq_str = "001"
        
        # 构建完整的资产编号
        new_asset_number = f"{asset_number_prefix}-{new_seq_str}"
        
        return jsonify({
            'success': True,
            'asset_number': new_asset_number
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成资产编号失败: {str(e)}'}), 500

# 设置路由
@asset.route('/devices/settings')
@login_required
def device_settings():
    return render_template('asset/device/settings.html')

# 分类设置
@asset.route('/devices/settings/categories')
@login_required
def device_categories():
    return render_template('asset/device/category.html')

# 获取分类列表
@asset.route('/api/asset/categories', methods=['GET'])
@login_required
def get_categories():
    categories = AssetCategory.query.order_by(AssetCategory.level, AssetCategory.id).all()
    
    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'level': category.level,
            'parent_id': category.parent_id,
            'code': category.code,
            'description': category.description
        })
    
    return jsonify({'success': True, 'data': result})

# 保存分类
@asset.route('/api/asset/categories', methods=['POST'])
@login_required
def save_category():
    data = request.json
    
    category_id = data.get('id')
    if category_id:
        category = AssetCategory.query.get_or_404(category_id)
    else:
        category = AssetCategory()
    
    # 必填项检查
    if not data.get('name'):
        return jsonify({'success': False, 'message': '分类名称不能为空'}), 400
    
    if not data.get('code'):
        return jsonify({'success': False, 'message': '分类编码不能为空'}), 400
    
    # 设置属性
    for key, value in data.items():
        if key != 'id' and hasattr(category, key):
            setattr(category, key, value)
    
    # 保存
    try:
        if not category_id:
            db.session.add(category)
        db.session.commit()
        return jsonify({'success': True, 'message': '保存成功', 'id': category.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 删除分类
@asset.route('/api/asset/categories/<int:id>', methods=['DELETE'])
@login_required
def delete_category(id):
    category = AssetCategory.query.get_or_404(id)
    
    # 检查是否有子分类
    if AssetCategory.query.filter_by(parent_id=id).first():
        return jsonify({'success': False, 'message': '该分类下有子分类，无法删除'}), 400
    
    # 检查是否有设备使用该分类
    if Device.query.filter_by(category_id=id).first():
        return jsonify({'success': False, 'message': '该分类下有设备，无法删除'}), 400
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 字段设置
@asset.route('/devices/settings/fields')
@login_required
def device_fields():
    return render_template('asset/device/field.html')

# 系统内置字段列表
SYSTEM_FIELD_KEYS = ['category_id', 'asset_number', 'device_number', 'name', 'model', 'serial_number', 'status', 
                     'security_level', 'user_id', 'department_id', 'location_id', 'purchase_date', 
                     'activation_date', 'mac_address', 'ip_address', 'operating_system', 
                     'installation_date', 'disk_serial', 'purpose', 'remarks', 'is_fixed_asset', 
                     'card_number', 'secret_inventory', 'inventory_category', 'qr_code']

# 获取系统默认字段列表
@asset.route('/api/asset/system-fields', methods=['GET'])
@login_required
def get_system_fields():
    # 定义设备模型中的默认字段，包含字段名、键名和类型等信息
    # 按照指定的默认排序顺序定义
    system_fields = [
        # 1. 分类
        {
            'name': '分类',
            'field_key': 'category_id',
            'field_type': 'select',
            'is_required': True,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 2. 资产编号
        {
            'name': '资产编号',
            'field_key': 'asset_number',
            'field_type': 'text',
            'is_required': True,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 3. 设备编号
        {
            'name': '设备编号',
            'field_key': 'device_number',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 4. 名称
        {
            'name': '设备名称',
            'field_key': 'name',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 5. 型号
        {
            'name': '设备型号',
            'field_key': 'model',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 6. 序列号
        {
            'name': '序列号',
            'field_key': 'serial_number',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 7. 设备状态
        {
            'name': '设备状态',
            'field_key': 'status',
            'field_type': 'select',
            'is_required': True,
            'is_visible': True,
            'options': json.dumps(['正常', '维修中', '已报废', '借出', '丢失']),
            'is_system': True
        },
        # 8. 密级
        {
            'name': '密级',
            'field_key': 'security_level',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': json.dumps(['非密', '内部', '秘密', '机密', '绝密']),
            'is_system': True
        },
        # 9. 用户
        {
            'name': '使用人',
            'field_key': 'user_id',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 10. 部门
        {
            'name': '部门',
            'field_key': 'department_id',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 11. 位置
        {
            'name': '位置',
            'field_key': 'location_id',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 12. 购入日期
        {
            'name': '购入日期',
            'field_key': 'purchase_date',
            'field_type': 'date',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 13. 启用时间
        {
            'name': '启用时间',
            'field_key': 'activation_date',
            'field_type': 'date',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 14. MAC
        {
            'name': 'MAC地址',
            'field_key': 'mac_address',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 15. IP
        {
            'name': 'IP地址',
            'field_key': 'ip_address',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 16. 操作系统
        {
            'name': '操作系统',
            'field_key': 'operating_system',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 17. 安装时间
        {
            'name': '安装时间',
            'field_key': 'installation_date',
            'field_type': 'date',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 18. 硬盘序列号
        {
            'name': '硬盘序列号',
            'field_key': 'disk_serial',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 19. 用途
        {
            'name': '用途',
            'field_key': 'purpose',
            'field_type': 'textarea',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 20. 备注
        {
            'name': '备注',
            'field_key': 'remarks',
            'field_type': 'textarea',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 21. 固资在账
        {
            'name': '固资在账',
            'field_key': 'is_fixed_asset',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': json.dumps(['是', '否']),
            'is_system': True
        },
        # 22. 卡片编号
        {
            'name': '卡片编号',
            'field_key': 'card_number',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 23. 保密台账
        {
            'name': '保密台账',
            'field_key': 'secret_inventory',
            'field_type': 'select',
            'is_required': False,
            'is_visible': True,
            'options': json.dumps(['是', '否']),
            'is_system': True
        },
        # 24. 台账分类
        {
            'name': '台账分类',
            'field_key': 'inventory_category',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        },
        # 25. 二维码
        {
            'name': '二维码',
            'field_key': 'qr_code',
            'field_type': 'text',
            'is_required': False,
            'is_visible': True,
            'options': None,
            'is_system': True
        }
    ]

    # 从数据库中查询设备字段配置，并与系统默认字段合并
    db_fields = DeviceField.query.all()
    db_field_keys = {field.field_key: field for field in db_fields}
    
    # 使用数据库中的设置更新系统字段(只更新可见性和必填状态)
    result = []
    for idx, field in enumerate(system_fields):
        field_key = field['field_key']
        if field_key in db_field_keys:
            # 更新系统字段信息
            db_field = db_field_keys[field_key]
            field['id'] = db_field.id
            field['is_visible'] = db_field.is_visible
            field['is_required'] = db_field.is_required
            field['sort_order'] = db_field.sort_order
            # 从数据库字段列表中移除，剩下的就是自定义字段
            db_field_keys.pop(field_key)
        else:
            # 为未在数据库中配置的系统字段设置默认ID和排序
            field['id'] = idx + 1
            field['sort_order'] = idx + 1
            
        result.append(field)
    
    return jsonify({'success': True, 'data': result})

# 获取自定义字段列表
@asset.route('/api/asset/custom-fields', methods=['GET'])
@login_required
def get_custom_fields():
    # 查询非系统字段
    fields = DeviceField.query.filter(~DeviceField.field_key.in_(SYSTEM_FIELD_KEYS)).order_by(DeviceField.sort_order).all()
    
    result = []
    for field in fields:
        result.append({
            'id': field.id,
            'name': field.name,
            'field_key': field.field_key,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'is_visible': field.is_visible,
            'options': field.options,
            'sort_order': field.sort_order,
            'is_system': False
        })
    
    return jsonify({'success': True, 'data': result})

# 获取所有字段列表(系统默认+自定义)
@asset.route('/api/asset/fields', methods=['GET'])
@login_required
def get_fields():
    # 获取系统字段
    system_fields_response = get_system_fields()
    system_fields = json.loads(system_fields_response.data).get('data', [])
    
    # 获取自定义字段
    custom_fields_response = get_custom_fields()
    custom_fields = json.loads(custom_fields_response.data).get('data', [])
    
    # 合并字段并按排序字段排序
    all_fields = system_fields + custom_fields
    sorted_fields = sorted(all_fields, key=lambda x: x.get('sort_order', 999))
    
    return jsonify({'success': True, 'data': sorted_fields})

# 保存字段
@asset.route('/api/asset/fields', methods=['POST'])
@login_required
def save_field():
    data = request.json
    
    field_id = data.get('id')
    is_system = data.get('is_system', False)
    field_key = data.get('field_key')
    
    # 特殊字段列表，这些字段不能修改类型和选项
    special_fields = ['category_id', 'asset_number', 'status', 'location_id', 'qr_code']
    is_special_field = field_key in special_fields
    
    # 如果是系统字段或特殊字段，只更新可见性和必填状态
    if is_system or is_special_field:
        # 查询是否已存在配置记录
        field = DeviceField.query.filter_by(field_key=field_key).first()
        
        # 如果不存在，则创建记录
        if not field:
            field = DeviceField(
                name=data.get('name'),
                field_key=field_key,
                field_type=data.get('field_type', 'text'),
                options=data.get('options')
            )
            db.session.add(field)
        
        # 更新可配置的属性
        field.is_visible = data.get('is_visible', True)
        field.is_required = data.get('is_required', False)
    else:
        # 自定义字段的保存逻辑
        if field_id:
            field = DeviceField.query.get_or_404(field_id)
        else:
            field = DeviceField()
        
        # 必填项检查
        if not data.get('name'):
            return jsonify({'success': False, 'message': '字段名称不能为空'}), 400
        
        if not data.get('field_key'):
            return jsonify({'success': False, 'message': '字段键名不能为空'}), 400
        
        # 设置属性
        for key, value in data.items():
            if key not in ['id', 'is_system'] and hasattr(field, key):
                setattr(field, key, value)
    
    # 保存
    try:
        db.session.commit()
        return jsonify({'success': True, 'message': '保存成功', 'id': field.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 删除字段
@asset.route('/api/asset/fields/<int:id>', methods=['DELETE'])
@login_required
def delete_field(id):
    field = DeviceField.query.get_or_404(id)
    
    # 检查是否为系统字段
    if field.field_key in SYSTEM_FIELD_KEYS:
        return jsonify({'success': False, 'message': '系统默认字段不能删除，但可以设为不可见'}), 400
    
    try:
        db.session.delete(field)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 更新字段排序
@asset.route('/api/asset/fields/update-order', methods=['POST'])
@login_required
def update_fields_order():
    try:
        data = request.json
        ordered_ids = data.get('ordered_ids', [])
        
        if not ordered_ids:
            return jsonify({'success': False, 'message': '无效的排序数据'}), 400
        
        # 逐个更新字段的排序值
        for idx, field_id in enumerate(ordered_ids):
            field = DeviceField.query.get(field_id)
            if field:
                field.sort_order = idx + 1  # 从1开始排序
        
        # 查找未在排序列表中的字段，可能是新添加的字段
        other_fields = DeviceField.query.filter(~DeviceField.id.in_(ordered_ids)).all()
        next_order = len(ordered_ids) + 1
        for field in other_fields:
            field.sort_order = next_order
            next_order += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': '字段排序更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新排序失败: {str(e)}'}), 500

# 位置设置
@asset.route('/devices/settings/locations')
@login_required
def device_locations():
    return render_template('asset/device/location.html')

# 获取位置列表
@asset.route('/api/asset/locations', methods=['GET'])
@login_required
def get_locations():
    locations = AssetLocation.query.order_by(AssetLocation.level, AssetLocation.id).all()
    
    result = []
    for location in locations:
        result.append({
            'id': location.id,
            'name': location.name,
            'level': location.level,
            'parent_id': location.parent_id,
            'code': location.code,
            'description': location.description,
            'map_data': location.map_data,
            'coordinate_x': location.coordinate_x,
            'coordinate_y': location.coordinate_y
        })
    
    return jsonify({'success': True, 'data': result})

# 保存位置
@asset.route('/api/asset/locations', methods=['POST'])
@login_required
def save_location():
    data = request.json
    
    location_id = data.get('id')
    if location_id:
        location = AssetLocation.query.get_or_404(location_id)
    else:
        location = AssetLocation()
    
    # 必填项检查
    if not data.get('name'):
        return jsonify({'success': False, 'message': '位置名称不能为空'}), 400
    
    if not data.get('code'):
        return jsonify({'success': False, 'message': '位置编码不能为空'}), 400
    
    # 设置属性
    for key, value in data.items():
        if key != 'id' and hasattr(location, key):
            setattr(location, key, value)
    
    # 保存
    try:
        if not location_id:
            db.session.add(location)
        db.session.commit()
        return jsonify({'success': True, 'message': '保存成功', 'id': location.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

# 删除位置
@asset.route('/api/asset/locations/<int:id>', methods=['DELETE'])
@login_required
def delete_location(id):
    location = AssetLocation.query.get_or_404(id)
    
    # 检查是否有子位置
    if AssetLocation.query.filter_by(parent_id=id).first():
        return jsonify({'success': False, 'message': '该位置下有子位置，无法删除'}), 400
    
    # 检查是否有设备使用该位置
    if Device.query.filter_by(location_id=id).first():
        return jsonify({'success': False, 'message': '该位置下有设备，无法删除'}), 400
    
    try:
        db.session.delete(location)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500

# 设备地图
@asset.route('/devices/map')
@login_required
def device_map():
    return render_template('asset/device/map.html') 