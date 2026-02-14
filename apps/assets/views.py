from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
import json
import qrcode
import os
import uuid
from io import BytesIO
import random
from datetime import datetime

from .models import (
    Device, AssetCategory, AssetLocation, DeviceField, DeviceFieldValue,
    Workstation, MapElement, MapBackground, LocationAreaBinding,
    Software, SoftwareCategory, SoftwareLicense,
    Consumable, ConsumableCategory, ConsumableRecord,
    ServiceType, ServiceRequest, ServiceLog, AssetLog
)
from apps.accounts.models import User, Department


def build_location_tree(location):
    children = location.children.all().order_by('sort', 'code')
    return {
        'id': location.id,
        'name': location.name,
        'code': location.code,
        'level': location.level,
        'children': [build_location_tree(child) for child in children]
    }


def get_location_tree_data():
    roots = AssetLocation.objects.filter(parent__isnull=True).order_by('sort', 'code')
    return [build_location_tree(loc) for loc in roots]


@login_required
def device_list(request):
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    location_id = request.GET.get('location', '')
    status = request.GET.get('status', '')
    
    devices = Device.objects.select_related('category', 'location', 'user', 'department').all()
    
    if search:
        devices = devices.filter(
            Q(asset_no__icontains=search) | 
            Q(name__icontains=search) | 
            Q(serial_no__icontains=search) |
            Q(device_no__icontains=search)
        )
    if category_id:
        devices = devices.filter(category_id=category_id)
    if location_id:
        devices = devices.filter(location_id=location_id)
    if status:
        devices = devices.filter(status=status)
    
    paginator = Paginator(devices, 20)
    page = request.GET.get('page', 1)
    devices = paginator.get_page(page)
    
    categories = AssetCategory.objects.filter(parent__isnull=True).prefetch_related('children')
    locations = AssetLocation.objects.filter(parent__isnull=True).prefetch_related('children')
    
    visible_fields = DeviceField.objects.filter(is_visible=True).order_by('sort')
    
    return render(request, 'assets/device_list.html', {
        'devices': devices,
        'categories': categories,
        'locations': locations,
        'visible_fields': visible_fields,
    })


@login_required
def device_create(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        category = AssetCategory.objects.get(pk=category_id)
        
        asset_no = generate_asset_no(category)
        
        device = Device.objects.create(
            asset_no=asset_no,
            device_no=request.POST.get('device_no'),
            serial_no=request.POST.get('serial_no'),
            name=request.POST.get('name'),
            model=request.POST.get('model'),
            category=category,
            status=request.POST.get('status', 'normal'),
            secret_level=request.POST.get('secret_level', 'public'),
            user_id=request.POST.get('user') or None,
            department_id=request.POST.get('department') or None,
            location_id=request.POST.get('location') or None,
            workstation_id=request.POST.get('workstation') or None,
            purchase_date=request.POST.get('purchase_date') or None,
            enable_date=request.POST.get('enable_date') or None,
            install_date=request.POST.get('install_date') or None,
            mac_address=request.POST.get('mac_address'),
            ip_address=request.POST.get('ip_address'),
            os_name=request.POST.get('os_name'),
            disk_serial=request.POST.get('disk_serial'),
            purpose=request.POST.get('purpose'),
            remarks=request.POST.get('remarks'),
            is_fixed=request.POST.get('is_fixed') == 'on',
            asset_card_no=request.POST.get('asset_card_no'),
            is_secret=request.POST.get('is_secret') == 'on',
            secret_category=request.POST.get('secret_category'),
            created_by=request.user,
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f'/device/scan/{device.id}')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        device.qrcode.save(f'{asset_no}.png', buffer)
        
        if request.FILES.get('photo'):
            save_photo_with_asset_no(device, request.FILES.get('photo'))
        
        AssetLog.objects.create(
            device=device,
            user=request.user,
            action='create',
            new_value='新增设备',
            remarks=f'资产编号: {asset_no}'
        )
        
        messages.success(request, f'设备创建成功，资产编号: {asset_no}')
        return redirect('device_list')
    
    categories = AssetCategory.objects.filter(parent__isnull=True).prefetch_related('children')
    locations = AssetLocation.objects.all()
    users = User.objects.all()
    departments = Department.objects.all()
    return render(request, 'assets/device_form.html', {
        'categories': categories,
        'locations': locations,
        'users': users,
        'departments': departments,
        'device': None,
    })


@login_required
def device_edit(request, pk):
    device = get_object_or_404(Device, pk=pk)
    
    if request.method == 'POST':
        old_values = {
            'name': device.name,
            'category': str(device.category),
            'status': device.status,
            'user': str(device.user) if device.user else '',
            'location': str(device.location) if device.location else '',
        }
        
        device.name = request.POST.get('name')
        device.device_no = request.POST.get('device_no')
        device.serial_no = request.POST.get('serial_no')
        device.model = request.POST.get('model')
        device.category_id = request.POST.get('category')
        device.status = request.POST.get('status', 'normal')
        device.secret_level = request.POST.get('secret_level', 'public')
        device.user_id = request.POST.get('user') or None
        device.department_id = request.POST.get('department') or None
        device.location_id = request.POST.get('location') or None
        device.workstation_id = request.POST.get('workstation') or None
        device.purchase_date = request.POST.get('purchase_date') or None
        device.enable_date = request.POST.get('enable_date') or None
        device.install_date = request.POST.get('install_date') or None
        device.mac_address = request.POST.get('mac_address')
        device.ip_address = request.POST.get('ip_address')
        device.os_name = request.POST.get('os_name')
        device.disk_serial = request.POST.get('disk_serial')
        device.purpose = request.POST.get('purpose')
        device.remarks = request.POST.get('remarks')
        device.is_fixed = request.POST.get('is_fixed') == 'on'
        device.asset_card_no = request.POST.get('asset_card_no')
        device.is_secret = request.POST.get('is_secret') == 'on'
        device.secret_category = request.POST.get('secret_category')
        
        # Handle file uploads
        if request.FILES.get('qrcode'):
            device.qrcode = request.FILES.get('qrcode')
        elif request.POST.get('qrcode_clear') == '1':
            device.qrcode.delete(save=False)
            device.qrcode = ''
        
        if request.FILES.get('photo'):
            if device.photo:
                device.photo.delete(save=False)
            save_photo_with_asset_no(device, request.FILES.get('photo'))
        elif request.POST.get('photo_clear') == '1':
            device.photo.delete(save=False)
            device.photo = ''
        
        device.save()
        
        for field, old_val in old_values.items():
            new_val = str(getattr(device, field))
            if old_val != new_val:
                AssetLog.objects.create(
                    device=device,
                    user=request.user,
                    action='update',
                    field_name=field,
                    old_value=old_val,
                    new_value=new_val,
                )
        
        messages.success(request, '设备更新成功')
        return redirect('device_list')
    
    categories = AssetCategory.objects.filter(parent__isnull=True).prefetch_related('children')
    locations = AssetLocation.objects.all()
    users = User.objects.all()
    departments = Department.objects.all()
    return render(request, 'assets/device_form.html', {
        'device': device,
        'categories': categories,
        'locations': locations,
        'users': users,
        'departments': departments,
    })


@login_required
def device_detail(request, pk):
    device = get_object_or_404(Device.objects.select_related('category', 'location', 'user', 'department', 'workstation'), pk=pk)
    logs = device.logs.all()[:20]
    all_fields = DeviceField.objects.all().order_by('sort')
    return render(request, 'assets/device_detail.html', {'device': device, 'logs': logs, 'all_fields': all_fields})


@login_required
def device_delete(request, pk):
    if request.method == 'POST':
        device = get_object_or_404(Device, pk=pk)
        AssetLog.objects.create(
            device=device,
            user=request.user,
            action='delete',
            old_value=str(device),
        )
        device.delete()
        messages.success(request, '设备删除成功')
    return redirect('device_list')


@login_required
def device_batch_delete(request):
    if request.method == 'POST':
        ids = request.POST.get('ids', '').split(',')
        count = Device.objects.filter(id__in=ids).delete()[0]
        messages.success(request, f'已删除 {count} 台设备')
    return redirect('device_list')


@login_required
def device_batch_assign(request):
    if request.method == 'POST':
        ids = request.POST.get('ids', '').split(',')
        user_id = request.POST.get('user_id')
        device_ids = [int(i) for i in ids if i]
        
        devices = Device.objects.filter(id__in=device_ids)
        for device in devices:
            device.user_id = user_id
            device.status = 'normal'
            device.save()
            AssetLog.objects.create(
                device=device,
                user=request.user,
                action='assign',
                new_value=f'分配给 {User.objects.get(pk=user_id).realname}',
            )
        
        messages.success(request, f'已分配 {len(device_ids)} 台设备')
    return redirect('device_list')


@login_required
def device_batch_fault(request):
    if request.method == 'POST':
        ids = request.POST.get('ids', '').split(',')
        device_ids = [int(i) for i in ids if i]
        
        devices = Device.objects.filter(id__in=device_ids)
        for device in devices:
            device.status = 'fault'
            device.save()
            AssetLog.objects.create(
                device=device,
                user=request.user,
                action='repair',
                new_value='标记为故障',
            )
        
        messages.success(request, f'已标记 {len(device_ids)} 台设备为故障')
    return redirect('device_list')


@login_required
def device_batch_scrap(request):
    if request.method == 'POST':
        ids = request.POST.get('ids', '').split(',')
        device_ids = [int(i) for i in ids if i]
        
        devices = Device.objects.filter(id__in=device_ids)
        for device in devices:
            device.status = 'scrapped'
            device.save()
            AssetLog.objects.create(
                device=device,
                user=request.user,
                action='scrap',
                new_value='标记为报废',
            )
        
        messages.success(request, f'已标记 {len(device_ids)} 台设备为报废')
    return redirect('device_list')


@login_required
def device_print_label(request, pk):
    device = get_object_or_404(Device, pk=pk)
    return render(request, 'assets/device_label.html', {'device': device})


@login_required
def device_scan(request, device_id):
    device = get_object_or_404(Device.objects.select_related('category', 'location', 'user'), pk=device_id)
    return render(request, 'assets/device_scan.html', {'device': device})


def generate_asset_no(category):
    prefix = category.get_full_code()
    last_device = Device.objects.filter(asset_no__startswith=prefix).order_by('-asset_no').first()
    
    if last_device:
        try:
            last_num = int(last_device.asset_no.split('-')[-1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    return f"{prefix}-{new_num:03d}"


def save_photo_with_asset_no(device, photo_file):
    if not photo_file:
        return
    
    ext = os.path.splitext(photo_file.name)[1].lower()
    filename = f"{device.asset_no}{ext}"
    device.photo.save(filename, photo_file, save=True)


@login_required
def category_list(request):
    categories = AssetCategory.objects.filter(
        parent__isnull=True
    ).prefetch_related(
        'children__children__children',
        'children__children',
        'children',
        'devices'
    ).order_by('sort', 'code', 'id')
    return render(request, 'assets/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        parent_id = request.POST.get('parent')
        description = request.POST.get('description')
        sort = request.POST.get('sort', 0)
        
        level = 1
        if parent_id:
            parent = AssetCategory.objects.filter(pk=parent_id).first()
            if parent:
                level = parent.level + 1
        
        if code and AssetCategory.objects.filter(code=code).exists():
            messages.error(request, '分类编码已存在')
        else:
            AssetCategory.objects.create(
                name=name,
                code=code,
                parent_id=parent_id if parent_id else None,
                level=level,
                description=description,
                sort=sort
            )
            messages.success(request, '分类创建成功')
            return redirect('category_list')
    
    categories = AssetCategory.objects.all()
    return render(request, 'assets/category_form.html', {'categories': categories})


@login_required
def category_edit(request, pk):
    category = get_object_or_404(AssetCategory, pk=pk)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.code = request.POST.get('code')
        parent_id = request.POST.get('parent') or None
        
        if parent_id:
            parent = AssetCategory.objects.filter(pk=parent_id).first()
            if parent:
                category.level = parent.level + 1
        else:
            category.level = 1
        
        category.parent_id = parent_id
        category.description = request.POST.get('description')
        category.sort = request.POST.get('sort', 0)
        category.save()
        messages.success(request, '分类更新成功')
        return redirect('category_list')
    
    categories = AssetCategory.objects.exclude(pk=pk)
    return render(request, 'assets/category_form.html', {'category': category, 'categories': categories})


@login_required
def category_delete(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(AssetCategory, pk=pk)
        if category.children.exists() or category.devices.exists():
            messages.error(request, '该分类下有子分类或设备，无法删除')
        else:
            category.delete()
            messages.success(request, '分类删除成功')
    return redirect('category_list')


@login_required
def location_list(request):
    locations = AssetLocation.objects.filter(
        parent__isnull=True
    ).prefetch_related(
        'children__children__children',
        'children__children',
        'children',
        'workstations',
        'devices'
    ).order_by('sort', 'code', 'id')
    return render(request, 'assets/location_list.html', {'locations': locations})


@login_required
def location_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        level = int(request.POST.get('level', 1))
        park_code = request.POST.get('park_code', '').strip().upper()
        building_code = request.POST.get('building_code', '').strip().upper()
        floor_code = request.POST.get('floor_code', '').strip()
        room_code = request.POST.get('room_code', '').strip()
        floor_count = int(request.POST.get('floor_count', 1))
        basement_count = int(request.POST.get('basement_count', 0))
        has_rooftop = request.POST.get('has_rooftop') == 'on'
        description = request.POST.get('description', '')
        sort = int(request.POST.get('sort', 0))
        
        parent = AssetLocation.objects.get(pk=parent_id) if parent_id else None
        if parent:
            level = parent.level + 1
            park_code = parent.code if parent.code else park_code
        
        if level == 1:
            code = park_code if park_code else f"LOC{AssetLocation.objects.count() + 1:03d}"
        elif level == 2:
            parent_code = parent.code if parent and parent.code else ''
            code = f"{parent_code}{building_code}" if parent_code and building_code else f"LOC{AssetLocation.objects.count() + 1:03d}"
        elif level == 3:
            prefix = parent.code if parent and parent.code else "LOC"
            max_floor = AssetLocation.objects.filter(parent=parent).count() if parent else 0
            code = f"{prefix}-{max_floor + 1:02d}"
        elif level == 4:
            prefix = parent.code if parent and parent.code else "LOC"
            code = f"{prefix}-{room_code}" if room_code else f"{prefix}-{AssetLocation.objects.count() + 1:03d}"
        else:
            code = f"LOC{AssetLocation.objects.count() + 1:03d}"
        
        if AssetLocation.objects.filter(code=code).exists():
            messages.error(request, '位置编码已存在')
        else:
            new_location = AssetLocation.objects.create(
                name=name,
                code=code,
                parent=parent,
                level=level,
                park_code=park_code,
                building_code=building_code,
                floor_code=floor_code,
                floor_count=floor_count,
                basement_count=basement_count,
                has_rooftop=has_rooftop,
                description=description,
                sort=sort
            )
            
            if level == 2 and (floor_count > 0 or basement_count > 0 or has_rooftop):
                sort_order = 0
                for i in range(1, basement_count + 1):
                    floor_name = f"B{i}层"
                    floor_code_val = f"B{i}"
                    floor_code_full = f"{code}{floor_code_val}"
                    sort_order += 1
                    AssetLocation.objects.create(
                        name=floor_name,
                        code=floor_code_full,
                        parent=new_location,
                        level=3,
                        park_code=park_code,
                        building_code=building_code,
                        floor_code=floor_code_val,
                        description=f"{name} {floor_name}",
                        sort=sort_order
                    )
                
                for i in range(1, floor_count + 1):
                    floor_name = f"{i}楼"
                    floor_code_val = f"{i:02d}"
                    floor_code_full = f"{code}{floor_code_val}"
                    sort_order += 1
                    AssetLocation.objects.create(
                        name=floor_name,
                        code=floor_code_full,
                        parent=new_location,
                        level=3,
                        park_code=park_code,
                        building_code=building_code,
                        floor_code=floor_code_val,
                        description=f"{name} {floor_name}",
                        sort=sort_order
                    )
                
                if has_rooftop:
                    sort_order += 1
                    AssetLocation.objects.create(
                        name="天台",
                        code=f"{code}C1",
                        parent=new_location,
                        level=3,
                        park_code=park_code,
                        building_code=building_code,
                        floor_code="C1",
                        description=f"{name} 天台",
                        sort=sort_order
                    )
                
                total_floors = basement_count + floor_count + (1 if has_rooftop else 0)
                msg_parts = []
                if basement_count > 0:
                    msg_parts.append(f"地下{basement_count}层")
                if floor_count > 0:
                    msg_parts.append(f"地上{floor_count}层")
                if has_rooftop:
                    msg_parts.append("天台")
                messages.success(request, f'位置创建成功，已自动生成 {total_floors} 个楼层（{"，".join(msg_parts)}）')
            else:
                messages.success(request, '位置创建成功')
            
            return redirect('location_list')
    
    locations = AssetLocation.objects.all()
    return render(request, 'assets/location_form.html', {'locations': locations})


@login_required
def location_edit(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    
    if request.method == 'POST':
        location.name = request.POST.get('name')
        parent_id = request.POST.get('parent') or None
        if parent_id:
            parent = AssetLocation.objects.get(pk=parent_id)
            location.level = parent.level + 1
            location.parent = parent
        
        park_code = request.POST.get('park_code', '').strip().upper()
        building_code = request.POST.get('building_code', '').strip().upper()
        floor_code = request.POST.get('floor_code', '').strip()
        room_code = request.POST.get('room_code', '').strip()
        
        if location.level == 1:
            location.code = park_code if park_code else location.code
        elif location.level == 2:
            location.code = f"{park_code}{building_code}" if park_code and building_code else location.code
        elif location.level == 4 and room_code:
            parent = location.parent
            prefix = parent.code if parent and parent.code else "LOC"
            location.code = f"{prefix}-{room_code}"
        
        location.park_code = park_code
        location.building_code = building_code
        location.floor_code = floor_code
        location.room_code = room_code
        location.floor_count = int(request.POST.get('floor_count', 1))
        location.basement_count = int(request.POST.get('basement_count', 0))
        location.has_rooftop = request.POST.get('has_rooftop') == 'on'
        location.map_width = int(request.POST.get('map_width', 1200))
        location.map_height = int(request.POST.get('map_height', 800))
        location.grid_size = int(request.POST.get('grid_size', 50))
        location.has_map = request.POST.get('has_map') == 'on'
        location.default_doorstop_width = float(request.POST.get('default_doorstop_width', 15))
        location.default_snap_threshold = float(request.POST.get('default_snap_threshold', 10))
        location.default_snap_enabled = request.POST.get('default_snap_enabled') == 'on'
        location.description = request.POST.get('description', '')
        location.sort = int(request.POST.get('sort', 0))
        location.save()
        messages.success(request, '位置更新成功')
        return redirect('location_list')
    
    locations = AssetLocation.objects.exclude(pk=pk)
    return render(request, 'assets/location_form.html', {'location': location, 'locations': locations})


from django.views.decorators.http import require_POST


@login_required
@require_POST
def location_delete(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    if location.children.exists() or location.devices.exists() or location.workstations.exists():
        messages.error(request, f'该位置下有子位置、设备或工位，无法删除')
    else:
        location.delete()
        messages.success(request, '位置删除成功')
    return redirect('location_list')


@login_required
def device_map(request):
    locations = AssetLocation.objects.filter(
        level=3, 
        has_map=True
    ).select_related('parent__parent', 'parent').prefetch_related('workstations', 'devices')
    
    location_list = []
    for loc in locations:
        location_list.append({
            'id': loc.id,
            'name': loc.name,
            'full_path': loc.get_full_path(),
            'workstation_count': loc.workstations.count(),
            'device_count': loc.devices.count(),
        })
    
    return render(request, 'assets/device_map.html', {
        'locations': location_list,
    })


@login_required
def location_map(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    elements = location.map_elements.all()
    workstation = location.workstations.all()
    area_bindings = LocationAreaBinding.objects.filter(parent_location=location)
    
    try:
        background = location.background
    except MapBackground.DoesNotExist:
        background = None
    
    return render(request, 'assets/location_map.html', {
        'location': location,
        'elements': elements,
        'workstations': workstation,
        'background': background,
        'area_bindings': area_bindings,
    })


@login_required
def field_list(request):
    fields = DeviceField.objects.all()
    return render(request, 'assets/field_list.html', {'fields': fields})


@login_required
def field_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        field_key = request.POST.get('field_key')
        field_type = request.POST.get('field_type')
        category_id = request.POST.get('category')
        is_required = request.POST.get('is_required') == 'on'
        is_visible = request.POST.get('is_visible') == 'on'
        options = request.POST.get('options')
        default_value = request.POST.get('default_value')
        sort = request.POST.get('sort', 0)
        
        DeviceField.objects.create(
            name=name,
            field_key=field_key,
            field_type=field_type,
            category_id=category_id if category_id else None,
            is_required=is_required,
            is_visible=is_visible,
            options=options,
            default_value=default_value,
            sort=sort,
        )
        messages.success(request, '字段创建成功')
        return redirect('field_list')
    
    categories = AssetCategory.objects.all()
    return render(request, 'assets/field_form.html', {'categories': categories})


@login_required
def field_edit(request, pk):
    field = get_object_or_404(DeviceField, pk=pk)
    
    if request.method == 'POST':
        field.name = request.POST.get('name')
        field.field_type = request.POST.get('field_type')
        field.category_id = request.POST.get('category') or None
        field.is_required = request.POST.get('is_required') == 'on'
        field.is_visible = request.POST.get('is_visible') == 'on'
        field.options = request.POST.get('options')
        field.default_value = request.POST.get('default_value')
        field.sort = request.POST.get('sort', 0)
        
        if not field.is_system:
            field.field_key = request.POST.get('field_key')
        
        field.save()
        messages.success(request, '字段更新成功')
        return redirect('field_list')
    
    categories = AssetCategory.objects.all()
    return render(request, 'assets/field_form.html', {'field': field, 'categories': categories})


@login_required
def field_delete(request, pk):
    if request.method == 'POST':
        field = get_object_or_404(DeviceField, pk=pk)
        if field.is_system:
            messages.error(request, '系统字段不能删除')
        else:
            field.delete()
            messages.success(request, '字段删除成功')
    return redirect('field_list')


@login_required
def software_list(request):
    software_list = Software.objects.all()
    return render(request, 'assets/software_list.html', {'software_list': software_list})


@login_required
def software_create(request):
    if request.method == 'POST':
        Software.objects.create(
            name=request.POST.get('name'),
            category_id=request.POST.get('category'),
            version=request.POST.get('version'),
            vendor=request.POST.get('vendor'),
            license_type=request.POST.get('license_type'),
            license_count=request.POST.get('license_count') or None,
            purchase_date=request.POST.get('purchase_date') or None,
            expire_date=request.POST.get('expire_date') or None,
            price=request.POST.get('price') or None,
            description=request.POST.get('description'),
        )
        messages.success(request, '软件创建成功')
        return redirect('software_list')
    
    categories = SoftwareCategory.objects.all()
    return render(request, 'assets/software_form.html', {'categories': categories})


@login_required
def consumable_list(request):
    consumables = Consumable.objects.all()
    return render(request, 'assets/consumable_list.html', {'consumables': consumables})


@login_required
def consumable_create(request):
    if request.method == 'POST':
        Consumable.objects.create(
            name=request.POST.get('name'),
            category_id=request.POST.get('category'),
            code=request.POST.get('code'),
            specification=request.POST.get('specification'),
            unit=request.POST.get('unit', '个'),
            stock_quantity=request.POST.get('stock_quantity', 0),
            min_stock=request.POST.get('min_stock', 0),
            price=request.POST.get('price') or None,
            description=request.POST.get('description'),
        )
        messages.success(request, '耗材创建成功')
        return redirect('consumable_list')
    
    categories = ConsumableCategory.objects.all()
    return render(request, 'assets/consumable_form.html', {'categories': categories})


@login_required
def service_list(request):
    requests = ServiceRequest.objects.all()
    return render(request, 'assets/service_list.html', {'requests': requests})


@login_required
def service_create(request):
    if request.method == 'POST':
        last_request = ServiceRequest.objects.order_by('-id').first()
        next_no = f"SR{timezone.now().strftime('%Y%m%d')}{int(last_request.id or 0) + 1:04d}" if last_request else f"SR{timezone.now().strftime('%Y%m%d')}0001"
        
        ServiceRequest.objects.create(
            request_no=next_no,
            title=request.POST.get('title'),
            service_type_id=request.POST.get('service_type'),
            description=request.POST.get('description'),
            priority=request.POST.get('priority', 'normal'),
            requester=request.user,
            device_id=request.POST.get('device') or None,
        )
        messages.success(request, '服务请求创建成功')
        return redirect('service_list')
    
    service_types = ServiceType.objects.all()
    devices = Device.objects.all()
    return render(request, 'assets/service_form.html', {'service_types': service_types, 'devices': devices})


@login_required
def api_get_code(request):
    category_id = request.GET.get('category_id')
    if category_id:
        try:
            category = AssetCategory.objects.get(pk=category_id)
            code = generate_asset_no(category)
            return JsonResponse({'code': code})
        except AssetCategory.DoesNotExist:
            pass
    return JsonResponse({'code': ''})


@login_required
def api_category_list(request):
    categories = AssetCategory.objects.order_by('level', 'id').all()
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
    return JsonResponse({'success': True, 'data': result})


@login_required
def api_category_save(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '无效请求'}), 400
    
    data = json.loads(request.body)
    category_id = data.get('id')
    
    if category_id:
        category = get_object_or_404(AssetCategory, pk=category_id)
    else:
        category = AssetCategory()
    
    if not data.get('name'):
        return JsonResponse({'success': False, 'message': '分类名称不能为空'}), 400
    
    if not data.get('code'):
        return JsonResponse({'success': False, 'message': '分类编码不能为空'}), 400
    
    category.name = data.get('name')
    category.code = data.get('code')
    category.description = data.get('description', '')
    category.sort = data.get('sort', 0)
    
    parent_id = data.get('parent_id')
    if parent_id:
        parent = AssetCategory.objects.get(pk=parent_id)
        category.parent = parent
        category.level = parent.level + 1
        if category.level > 4:
            return JsonResponse({'success': False, 'message': '分类最多支持4级'}), 400
    else:
        category.parent = None
        category.level = 1
    
    try:
        if not category_id:
            category.save()
        else:
            category.save()
        return JsonResponse({'success': True, 'message': '保存成功', 'id': category.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@login_required
def api_category_delete(request, id):
    category = get_object_or_404(AssetCategory, pk=id)
    
    if AssetCategory.objects.filter(parent_id=id).first():
        return JsonResponse({'success': False, 'message': '该分类下有子分类，无法删除'}), 400
    
    if Device.objects.filter(category_id=id).first():
        return JsonResponse({'success': False, 'message': '该分类下有设备，无法删除'}), 400
    
    try:
        category.delete()
        return JsonResponse({'success': True, 'message': '删除成功'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@login_required
def api_generate_asset_number(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '无效请求'}, status=400)
    
    data = json.loads(request.body)
    category_id = data.get('category_id')
    
    if not category_id:
        return JsonResponse({'success': False, 'message': '请选择分类'}, status=400)
    
    try:
        category = AssetCategory.objects.get(pk=category_id)
        
        # 使用 get_full_code() 获取完整的前缀（如 XACD-Z-001-001）
        asset_number_prefix = category.get_full_code()
        
        max_device = Device.objects.filter(
            asset_no__startswith=f"{asset_number_prefix}-"
        ).order_by('-asset_no').first()
        
        if max_device:
            last_part = max_device.asset_no.split('-')[-1]
            try:
                new_seq = int(last_part) + 1
                new_seq_str = f"{new_seq:03d}"
            except ValueError:
                new_seq_str = "001"
        else:
            new_seq_str = "001"
        
        new_asset_number = f"{asset_number_prefix}-{new_seq_str}"
        
        return JsonResponse({
            'success': True,
            'asset_number': new_asset_number
        })
    except AssetCategory.DoesNotExist:
        return JsonResponse({'success': False, 'message': '分类不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'生成资产编号失败: {str(e)}'}, status=500)


@login_required
def api_get_category_by_asset_no(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '无效请求'}, status=400)
    
    data = json.loads(request.body)
    asset_no = data.get('asset_no', '').strip()
    
    if not asset_no:
        return JsonResponse({'success': False, 'message': '请输入资产编号'}, status=400)
    
    parts = asset_no.split('-')
    if len(parts) < 2:
        return JsonResponse({'success': False, 'message': '资产编号格式不正确'}, status=400)
    
    prefix = '-'.join(parts[:-1])
    
    category = AssetCategory.find_by_asset_prefix(prefix)
    
    if not category:
        return JsonResponse({'success': False, 'message': '未找到匹配的分类'}, status=404)
    
    return JsonResponse({
        'success': True,
        'category_id': category.id,
        'category_name': category.name,
        'category_level': category.level,
        'full_code': category.get_full_code()
    })


@login_required
def device_stats(request):
    stats = {
        'total': Device.objects.count(),
        'normal': Device.objects.filter(status='normal').count(),
        'fault': Device.objects.filter(status='fault').count(),
        'repairing': Device.objects.filter(status='repairing').count(),
        'scrapped': Device.objects.filter(status='scrapped').count(),
        'unused': Device.objects.filter(status='unused').count(),
    }
    return JsonResponse(stats)


@login_required
def location_tree(request):
    def build_tree(location):
        children = location.children.all().order_by('sort', 'code')
        return {
            'id': location.id,
            'name': location.name,
            'code': location.code,
            'level': location.level,
            'park_code': location.park_code,
            'building_code': location.building_code,
            'floor_code': location.floor_code,
            'floor_count': location.floor_count,
            'room_code': location.room_code,
            'has_map': location.has_map,
            'map_width': location.map_width,
            'map_height': location.map_height,
            'children': [build_tree(child) for child in children]
        }
    
    roots = AssetLocation.objects.filter(parent__isnull=True).order_by('sort', 'code')
    tree_data = [build_tree(loc) for loc in roots]
    return JsonResponse({'data': tree_data})


@login_required
def map_data(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    
    elements = MapElement.objects.filter(location=location).values()
    workstations = Workstation.objects.filter(location=location).select_related('location')
    devices = Device.objects.filter(location=location).select_related('category', 'user', 'workstation')
    
    try:
        background = location.background
        bg_data = {
            'bg_type': background.bg_type,
            'scale': background.scale,
            'offset_x': background.offset_x,
            'offset_y': background.offset_y,
            'opacity': background.opacity,
        }
        if background.file_data:
            bg_data['file_data'] = background.file_data.decode('utf-8') if isinstance(background.file_data, bytes) else None
    except MapBackground.DoesNotExist:
        bg_data = None
    
    workstation_list = []
    for ws in workstations:
        ws_devices = devices.filter(workstation=ws)
        workstation_list.append({
            'id': ws.id,
            'workstation_code': ws.workstation_code,
            'name': ws.name,
            'x': ws.x,
            'y': ws.y,
            'width': ws.width,
            'height': ws.height,
            'status': ws.status,
            'devices': [
                {
                    'id': d.id,
                    'asset_no': d.asset_no,
                    'name': d.name,
                    'status': d.status,
                    'user': d.user.realname if d.user else None,
                }
                for d in ws_devices
            ]
        })
    
    device_list = devices.filter(workstation__isnull=True).values(
        'id', 'asset_no', 'name', 'status', 'category__name', 'user__realname'
    )
    
    return JsonResponse({
        'location': {
            'id': location.id,
            'name': location.name,
            'code': location.code,
            'level': location.level,
            'map_width': location.map_width,
            'map_height': location.map_height,
        },
        'background': bg_data,
        'elements': list(elements),
        'workstations': workstation_list,
        'devices': list(device_list),
        'area_bindings': [{
            'id': b.id,
            'location_id': b.location_id,
            'location_name': b.location.name,
            'area_name': b.area_name,
            'area_points': b.area_points,
            'area_color': b.area_color,
        } for b in LocationAreaBinding.objects.filter(parent_location=location)],
    })


@login_required
def map_element_save(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        
        elements_data = request.POST.get('elements')
        if elements_data:
            import json
            try:
                elements_list = json.loads(elements_data)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': '数据格式错误'})
            
            saved_ids = []
            for el_data in elements_list:
                el_id = el_data.get('id')
                data = {
                    'location_id': location_id,
                    'element_type': el_data.get('type', 'wall'),
                    'x': float(el_data.get('x', 0)),
                    'y': float(el_data.get('y', 0)),
                    'x2': float(el_data.get('x2')) if el_data.get('x2') else None,
                    'y2': float(el_data.get('y2')) if el_data.get('y2') else None,
                    'width': float(el_data.get('width', 0)),
                    'height': float(el_data.get('height', 0)),
                    'rotation': float(el_data.get('rotation', 0)),
                    'color': el_data.get('color', '#000000'),
                    'thickness': int(el_data.get('thickness', 2)),
                    'points': el_data.get('points', ''),
                    'properties': el_data.get('properties', ''),
                    'sort_order': int(el_data.get('sort_order', 0)),
                    'door_direction': el_data.get('door_direction', 'right'),
                    'door_width': float(el_data.get('door_width', 60)),
                    'door_open_angle': int(el_data.get('door_open_angle', 90)),
                    'doorstop_width': float(el_data.get('doorstop_width', 15)),
                    'auto_doorstop': el_data.get('auto_doorstop', True),
                    'snap_enabled': el_data.get('snap_enabled', True),
                    'snap_threshold': float(el_data.get('snap_threshold', 10)),
                }
                
                if el_id:
                    element = MapElement.objects.filter(pk=el_id).first()
                    if element:
                        for key, value in data.items():
                            setattr(element, key, value)
                        element.save()
                        saved_ids.append(element.id)
                else:
                    element = MapElement.objects.create(**data)
                    saved_ids.append(element.id)
            
            existing_ids = [int(el.get('id')) for el in elements_list if el.get('id')]
            MapElement.objects.filter(location_id=location_id).exclude(id__in=saved_ids).delete()
            
            return JsonResponse({'success': True, 'message': f'保存成功，共 {len(saved_ids)} 个元素', 'saved_ids': saved_ids})
        
        element_id = request.POST.get('element_id')
        
        data = {
            'location_id': location_id,
            'element_type': request.POST.get('element_type'),
            'x': float(request.POST.get('x', 0)),
            'y': float(request.POST.get('y', 0)),
            'x2': float(request.POST.get('x2')) if request.POST.get('x2') else None,
            'y2': float(request.POST.get('y2')) if request.POST.get('y2') else None,
            'width': float(request.POST.get('width', 0)),
            'height': float(request.POST.get('height', 0)),
            'rotation': float(request.POST.get('rotation', 0)),
            'color': request.POST.get('color', '#000000'),
            'thickness': int(request.POST.get('thickness', 2)),
            'points': request.POST.get('points', ''),
            'properties': request.POST.get('properties', ''),
            'sort_order': int(request.POST.get('sort_order', 0)),
            'door_direction': request.POST.get('door_direction', 'right'),
            'door_width': float(request.POST.get('door_width', 60)),
            'door_open_angle': int(request.POST.get('door_open_angle', 90)),
            'doorstop_width': float(request.POST.get('doorstop_width', 15)),
            'auto_doorstop': request.POST.get('auto_doorstop', 'true').lower() == 'true',
            'snap_enabled': request.POST.get('snap_enabled', 'true').lower() == 'true',
            'snap_threshold': float(request.POST.get('snap_threshold', 10)),
        }
        
        if element_id:
            element = get_object_or_404(MapElement, pk=element_id)
            for key, value in data.items():
                setattr(element, key, value)
            element.save()
            message = '元素更新成功'
        else:
            element = MapElement.objects.create(**data)
            message = '元素创建成功'
        
        return JsonResponse({'success': True, 'message': message, 'element_id': element.id})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def map_element_delete(request, pk):
    if request.method == 'POST':
        element = get_object_or_404(MapElement, pk=pk)
        element.delete()
        return JsonResponse({'success': True, 'message': '元素删除成功'})
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def map_background_upload(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    
    if request.method == 'POST':
        bg_type = request.POST.get('bg_type', 'image')
        file_data = request.FILES.get('file')
        scale = float(request.POST.get('scale', 1.0))
        offset_x = float(request.POST.get('offset_x', 0))
        offset_y = float(request.POST.get('offset_y', 0))
        opacity = float(request.POST.get('opacity', 1.0))
        
        bg_data = {
            'location': location,
            'bg_type': bg_type,
            'scale': scale,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'opacity': opacity,
        }
        
        if file_data:
            bg_data['file_data'] = file_data.read()
        
        MapBackground.objects.update_or_create(
            location=location,
            defaults=bg_data
        )
        
        AssetLocation.objects.filter(pk=pk).update(has_map=True)
        
        return JsonResponse({'success': True, 'message': '底图上传成功'})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def workstation_list(request, location_id):
    location = get_object_or_404(AssetLocation, pk=location_id)
    workstations = Workstation.objects.filter(location=location).prefetch_related('devices')
    return render(request, 'assets/workstation_list.html', {
        'location': location,
        'workstations': workstations,
    })


@login_required
def api_workstations_by_location(request, location_id):
    location = get_object_or_404(AssetLocation, pk=location_id)
    workstations = Workstation.objects.filter(location=location).values('id', 'name', 'workstation_code')
    return JsonResponse({
        'success': True,
        'workstations': list(workstations)
    })


@login_required
def workstation_create(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        location = get_object_or_404(AssetLocation, pk=location_id)
        
        code = generate_workstation_code(location)
        
        workstation = Workstation.objects.create(
            location=location,
            workstation_code=code,
            name=request.POST.get('name'),
            x=float(request.POST.get('x', 0)),
            y=float(request.POST.get('y', 0)),
            width=float(request.POST.get('width', 30)),
            height=float(request.POST.get('height', 20)),
            status=request.POST.get('status', 'available'),
            description=request.POST.get('description', ''),
        )
        
        messages.success(request, f'工位创建成功: {code}')
        return redirect('workstation_list', location_id=location_id)
    
    location_id = request.GET.get('location_id')
    location = get_object_or_404(AssetLocation, pk=location_id) if location_id else None
    locations = AssetLocation.objects.filter(level=4)
    return render(request, 'assets/workstation_form.html', {
        'location': location,
        'locations': locations,
    })


@login_required
def workstation_edit(request, pk):
    workstation = get_object_or_404(Workstation, pk=pk)
    
    if request.method == 'POST':
        workstation.name = request.POST.get('name')
        workstation.x = float(request.POST.get('x', 0))
        workstation.y = float(request.POST.get('y', 0))
        workstation.width = float(request.POST.get('width', 30))
        workstation.height = float(request.POST.get('height', 20))
        workstation.status = request.POST.get('status', 'available')
        workstation.description = request.POST.get('description', '')
        workstation.save()
        
        messages.success(request, '工位更新成功')
        return redirect('workstation_list', location_id=workstation.location_id)
    
    locations = AssetLocation.objects.filter(level=4)
    return render(request, 'assets/workstation_form.html', {
        'workstation': workstation,
        'location': workstation.location,
        'locations': locations,
    })


@login_required
def workstation_delete(request, pk):
    if request.method == 'POST':
        workstation = get_object_or_404(Workstation, pk=pk)
        location_id = workstation.location_id
        workstation.delete()
        messages.success(request, '工位删除成功')
        return redirect('workstation_list', location_id=location_id)
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def workstation_batch_create(request):
    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        location = get_object_or_404(AssetLocation, pk=location_id)
        
        rows = int(request.POST.get('rows', 1))
        cols = int(request.POST.get('cols', 1))
        start_x = float(request.POST.get('start_x', 0))
        start_y = float(request.POST.get('start_y', 0))
        spacing_x = float(request.POST.get('spacing_x', 50))
        spacing_y = float(request.POST.get('spacing_y', 40))
        width = float(request.POST.get('width', 30))
        height = float(request.POST.get('height', 20))
        
        prefix = location.code or f"L{location.id}"
        
        created = []
        for row in range(rows):
            for col in range(cols):
                code = generate_workstation_code(location, row * cols + col + 1)
                ws = Workstation.objects.create(
                    location=location,
                    workstation_code=code,
                    name=f"{prefix}-{row+1:02d}{col+1:02d}",
                    x=start_x + col * spacing_x,
                    y=start_y + row * spacing_y,
                    width=width,
                    height=height,
                    status='available',
                )
                created.append(ws.workstation_code)
        
        messages.success(request, f'成功创建 {len(created)} 个工位')
        return redirect('workstation_list', location_id=location_id)
    
    location_id = request.GET.get('location_id')
    location = get_object_or_404(AssetLocation, pk=location_id) if location_id else None
    locations = AssetLocation.objects.filter(level=4)
    return render(request, 'assets/workstation_batch.html', {'location': location, 'locations': locations})


def generate_workstation_code(location, seq=None):
    prefix = location.code or f"L{location.id}"
    
    if seq is None:
        last_ws = Workstation.objects.filter(location=location).order_by('-id').first()
        seq = (last_ws.id or 0) + 1 if last_ws else 1
    
    return f"{prefix}-{seq:04d}"


@login_required
def api_device_bind_workstation(request):
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        workstation_id = request.POST.get('workstation_id')
        
        device = get_object_or_404(Device, pk=device_id)
        
        if workstation_id:
            workstation = get_object_or_404(Workstation, pk=workstation_id)
            device.workstation = workstation
            device.location = workstation.location
            parts = []
            loc = workstation.location
            while loc:
                parts.insert(0, loc.name)
                loc = loc.parent
            parts.append(workstation.workstation_code)
            device.location_text = '-'.join(parts)
            workstation.status = 'occupied'
            workstation.save()
        else:
            device.workstation = None
        
        device.save()
        
        AssetLog.objects.create(
            device=device,
            user=request.user,
            action='update',
            field_name='workstation',
            old_value='',
            new_value=str(device.workstation) if device.workstation else '未绑定',
        )
        
        return JsonResponse({'success': True, 'message': '设备绑定成功'})
    
    return JsonResponse({'success': False, 'message': '无效请求'})


@login_required
def location_map(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    elements = location.map_elements.all()
    workstations = location.workstations.all()
    
    try:
        background = location.background
    except MapBackground.DoesNotExist:
        background = None
    
    all_locations = AssetLocation.objects.filter(level__lte=4).order_by('level', 'sort', 'id')
    
    def build_tree(loc):
        children = loc.children.all()
        return {
            'id': loc.id,
            'name': loc.name,
            'code': loc.code,
            'level': loc.level,
            'park_code': loc.park_code,
            'building_code': loc.building_code,
            'floor_code': loc.floor_code,
            'floor_count': loc.floor_count,
            'has_map': loc.has_map,
            'children': [build_tree(c) for c in children]
        }
    
    roots = AssetLocation.objects.filter(parent__isnull=True)
    location_tree = [build_tree(loc) for loc in roots]
    
    return render(request, 'assets/location_map.html', {
        'location': location,
        'elements': elements,
        'workstations': workstations,
        'background': background,
        'location_tree': location_tree,
        'all_locations': all_locations,
    })


@login_required
def location_map_edit(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    elements = location.map_elements.all()
    
    return render(request, 'assets/map_editor.html', {
        'location': location,
        'elements': elements,
    })


@login_required
@require_http_methods(["GET", "POST"])
def location_area_binding(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    
    if request.method == 'GET':
        child_locations = AssetLocation.objects.filter(parent=location, level=4)
        bindings = LocationAreaBinding.objects.filter(parent_location=location)
        binding_map = {b.location_id: b for b in bindings}
        
        return render(request, 'assets/location_area_binding.html', {
            'location': location,
            'child_locations': child_locations,
            'bindings': bindings,
            'binding_map': binding_map,
        })
    
    location_id = request.POST.get('location_id')
    area_points = request.POST.get('area_points', '[]')
    area_color = request.POST.get('area_color', '#3498db')
    area_name = request.POST.get('area_name', '')
    
    child_location = AssetLocation.objects.get(pk=location_id)
    
    binding, created = LocationAreaBinding.objects.update_or_create(
        location=child_location,
        parent_location=location,
        defaults={
            'area_points': area_points,
            'area_color': area_color,
            'area_name': area_name or child_location.name,
        }
    )
    
    messages.success(request, f'区域绑定成功: {binding.area_name}')
    return redirect('location_area_binding', pk=pk)


@login_required
def location_area_binding_delete(request, pk, binding_id):
    binding = get_object_or_404(LocationAreaBinding, pk=binding_id, parent_location_id=pk)
    binding.delete()
    messages.success(request, '区域绑定已删除')
    return redirect('location_area_binding', pk=pk)


@login_required
def api_location_area_bindings(request, pk):
    location = get_object_or_404(AssetLocation, pk=pk)
    bindings = LocationAreaBinding.objects.filter(parent_location=location)
    
    data = [{
        'id': b.id,
        'location_id': b.location_id,
        'location_name': b.location.name,
        'area_name': b.area_name,
        'area_points': b.area_points,
        'area_color': b.area_color,
    } for b in bindings]
    
    return JsonResponse({'success': True, 'bindings': data})
