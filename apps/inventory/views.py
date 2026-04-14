from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, F, Case, When, IntegerField
import json
import random
import re
import os
import threading
import uuid
import time

from .models import InventoryPlan, InventoryTask, InventoryRecord, InventoryTaskDevice
from apps.assets.models import Device, AssetLocation, AssetCategory
from apps.assets.views import save_photo_with_asset_no
from apps.accounts.models import User, Department
from apps.settings.views import get_config_value


# 设备导入进度存储
inventory_import_progress = {}


def inventory_add_log(task_id, level, message):
    """添加处理日志"""
    import datetime
    if task_id in inventory_import_progress:
        inventory_import_progress[task_id]['logs'].append({
            'time': datetime.datetime.now().strftime('%H:%M:%S'),
            'level': level,
            'message': message
        })


# ==================== 任务管理 ====================

@login_required
def task_list(request):
    """任务列表页"""
    status = request.GET.get('status', '')
    task_type = request.GET.get('task_type', '')
    search = request.GET.get('search', '')
    
    tasks = InventoryTask.objects.select_related('created_by', 'assignee').all()
    
    if status:
        tasks = tasks.filter(status=status)
    if task_type:
        tasks = tasks.filter(task_type=task_type)
    if search:
        tasks = tasks.filter(
            Q(task_no__icontains=search) |
            Q(name__icontains=search)
        )
    
    return render(request, 'inventory/task_list.html', {
        'tasks': tasks,
        'status_filter': status,
        'task_type_filter': task_type,
        'search': search,
    })


@login_required
def task_create(request):
    """创建盘点任务"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        task_type = request.POST.get('task_type', 'full')
        is_fixed_only = request.POST.get('is_fixed_only') == 'on'
        scheduled_start = request.POST.get('scheduled_start')
        scheduled_end = request.POST.get('scheduled_end')
        remarks = request.POST.get('remarks', '').strip()
        
        task = InventoryTask.objects.create(
            name=name,
            task_type=task_type,
            is_fixed_only=is_fixed_only,
            status='pending',
            created_by=request.user,
            scheduled_start=scheduled_start if scheduled_start else None,
            scheduled_end=scheduled_end if scheduled_end else None,
            remarks=remarks,
        )
        
        # 全盘和动态盘点自动生成设备列表
        if task_type in ('full', 'dynamic'):
            generate_task_devices(task)
        
        messages.success(request, f'盘点任务创建成功: {task.task_no}')
        return redirect('inventory_task_detail', pk=task.pk)
    
    return render(request, 'inventory/task_create.html')


@login_required
def task_detail(request, pk):
    """任务详情页（含待盘/已盘列表）"""
    task = get_object_or_404(InventoryTask.objects.select_related('created_by', 'assignee'), pk=pk)
    
    # 待盘点设备 - 有位置的在前，无位置的在后，按位置排序
    pending_devices = InventoryTaskDevice.objects.filter(
        task=task, status='pending'
    ).select_related(
        'device__category', 'device__location', 'device__user', 'device__department', 'device__workstation'
    ).annotate(
        has_location=Case(
            When(device__location_text='', then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by('has_location', 'device__location_text', 'device__id')
    
    # 已盘点设备
    checked_devices = InventoryTaskDevice.objects.filter(
        task=task, status='checked'
    ).select_related(
        'device__category', 'device__location', 'device__user', 'device__department', 'device__workstation'
    ).order_by('-checked_at')
    
    # 统计
    total_count = InventoryTaskDevice.objects.filter(task=task).count()
    pending_count = pending_devices.count()
    checked_count = checked_devices.count()
    
    return render(request, 'inventory/task_detail.html', {
        'task': task,
        'pending_devices': pending_devices,
        'checked_devices': checked_devices,
        'total_count': total_count,
        'pending_count': pending_count,
        'checked_count': checked_count,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def task_delete(request, pk):
    """删除任务"""
    task = get_object_or_404(InventoryTask, pk=pk)
    if task.status == 'completed':
        return JsonResponse({'success': False, 'message': '已完成的任务不能删除'})
    
    task.delete()
    messages.success(request, '任务已删除')
    return JsonResponse({'success': True})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def task_start(request, pk):
    """开始任务"""
    task = get_object_or_404(InventoryTask, pk=pk)
    if task.status != 'pending':
        return JsonResponse({'success': False, 'message': '只有待执行的任务才能开始'})
    
    device_count = InventoryTaskDevice.objects.filter(task=task).count()
    if device_count == 0:
        return JsonResponse({'success': False, 'message': '请先添加待盘点设备'})
    
    task.status = 'in_progress'
    task.device_count = device_count
    task.save()
    
    return JsonResponse({'success': True, 'message': '任务已开始'})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def task_complete(request, pk):
    """完成任务"""
    task = get_object_or_404(InventoryTask, pk=pk)
    if task.status != 'in_progress':
        return JsonResponse({'success': False, 'message': '只有执行中的任务才能完成'})
    
    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save()
    
    return JsonResponse({'success': True, 'message': '任务已完成'})


# ==================== 设备抽选 ====================

@login_required
def get_device_pool(request, task_id):
    """获取设备池（根据任务类型和筛选条件）"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    # 基础查询：排除报废设备
    devices = Device.objects.exclude(status='scrapped').select_related('category', 'location', 'user')
    
    # 固资在账筛选
    if task.is_fixed_only:
        devices = devices.filter(is_fixed=True)
    
    return devices


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_random_select(request, task_id):
    """随机抽选设备"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        select_type = data.get('select_type', 'percent')  # percent 或 count
        select_value = int(data.get('select_value', 0))
        
        if select_value <= 0:
            return JsonResponse({'success': False, 'message': '请输入有效的抽选值'})
        
        # 获取设备池
        devices = get_device_pool(request, task_id)
        
        # 排除已添加的设备
        existing_device_ids = InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True)
        devices = devices.exclude(id__in=existing_device_ids)
        
        device_list = list(devices)
        total_count = len(device_list)
        
        if total_count == 0:
            return JsonResponse({'success': False, 'message': '没有可抽选的设备'})
        
        # 计算抽选数量
        if select_type == 'percent':
            select_count = max(1, int(total_count * select_value / 100))
        else:
            select_count = min(select_value, total_count)
        
        # 随机抽选
        selected_devices = random.sample(device_list, select_count)
        
        # 添加到任务设备列表
        current_max_order = InventoryTaskDevice.objects.filter(task=task).count()
        for i, device in enumerate(selected_devices):
            InventoryTaskDevice.objects.create(
                task=task,
                device=device,
                status='pending',
                sort_order=current_max_order + i + 1,
                added_by=request.user,
            )
        
        # 更新设备计数
        task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'已随机抽选 {select_count} 台设备',
            'selected_count': select_count,
            'total_count': task.device_count,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def api_device_search(request, task_id):
    """搜索设备（人工抽选）"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    q = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # 获取设备池
    devices = get_device_pool(request, task_id)
    
    # 排除已添加的设备
    existing_device_ids = InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True)
    devices = devices.exclude(id__in=existing_device_ids)
    
    # 搜索
    if q:
        devices = devices.filter(
            Q(asset_no__icontains=q) |
            Q(name__icontains=q) |
            Q(serial_no__icontains=q) |
            Q(device_no__icontains=q) |
            Q(model__icontains=q) |
            Q(user__realname__icontains=q) |
            Q(department__name__icontains=q) |
            Q(location_text__icontains=q)
        ).distinct()
    
    # 分页
    paginator = Paginator(devices, page_size)
    page_obj = paginator.get_page(page)
    
    # 序列化
    device_list = []
    for d in page_obj:
        device_list.append({
            'id': d.id,
            'asset_no': d.asset_no,
            'device_no': d.device_no or '',
            'name': d.name,
            'model': d.model or '',
            'secret_level': d.get_secret_level_display(),
            'secret_level_code': d.secret_level,
            'department': d.department.name if d.department else '',
            'user': d.user.realname if d.user else '',
            'location': d.location.get_full_path() if d.location else '',
            'location_text': d.location_text or '',
            'status': d.get_status_display(),
            'status_code': d.status,
            'is_fixed': d.is_fixed,
            'asset_card_no': d.asset_card_no or '',
            'category': d.category.name if d.category else '',
        })
    
    return JsonResponse({
        'success': True,
        'devices': device_list,
        'total': paginator.count,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_add_devices(request, task_id):
    """添加设备到待盘列表"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        device_ids = data.get('device_ids', [])
        
        if not device_ids:
            return JsonResponse({'success': False, 'message': '请选择设备'})
        
        # 排除已添加的
        existing_ids = set(InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True))
        new_ids = [did for did in device_ids if did not in existing_ids]
        
        if not new_ids:
            return JsonResponse({'success': False, 'message': '所选设备已在待盘列表中'})
        
        # 获取最大排序号
        current_max_order = InventoryTaskDevice.objects.filter(task=task).count()
        
        # 批量创建
        devices = Device.objects.filter(id__in=new_ids)
        task_devices = []
        for i, device in enumerate(devices):
            task_devices.append(InventoryTaskDevice(
                task=task,
                device=device,
                status='pending',
                sort_order=current_max_order + i + 1,
                added_by=request.user,
            ))
        InventoryTaskDevice.objects.bulk_create(task_devices)
        
        # 更新计数
        task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': f'已添加 {len(new_ids)} 台设备',
            'added_count': len(new_ids),
            'total_count': task.device_count,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_remove_device(request, task_id):
    """从待盘列表移除设备"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        task_device_id = data.get('task_device_id')
        
        task_device = get_object_or_404(InventoryTaskDevice, pk=task_device_id, task=task)
        
        if task_device.status == 'checked':
            return JsonResponse({'success': False, 'message': '已盘点的设备不能移除'})
        
        task_device.delete()
        
        # 更新计数
        task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
        task.save()
        
        return JsonResponse({'success': True, 'message': '设备已移除'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ==================== AI解析导入 ====================

def expand_asset_no_pattern(asset_no_str):
    """
    解析类似 XACD-Z-001-001-001/003/007 的合并写法
    返回: ['XACD-Z-001-001-001', 'XACD-Z-001-001-003', 'XACD-Z-001-001-007']
    """
    asset_no_str = asset_no_str.strip()
    if not asset_no_str:
        return []
    
    if '/' not in asset_no_str:
        return [asset_no_str]
    
    parts = asset_no_str.split('/')
    base = parts[0].strip()
    
    if not base:
        return []
    
    # 找到最后一个 - 的位置
    last_dash = base.rfind('-')
    if last_dash == -1:
        return [base]
    
    prefix = base[:last_dash + 1]
    base_num = base[last_dash + 1:]
    
    result = [base]
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        # 如果是纯数字，保持与基础编号相同的位数
        if part.isdigit() and base_num.isdigit():
            padded = part.zfill(len(base_num))
            result.append(f"{prefix}{padded}")
        else:
            result.append(f"{prefix}{part}")
    
    return result


def parse_asset_numbers_with_ai(content, content_type='text'):
    """使用AI解析资产编号"""
    api_key = get_config_value('llm_api_key', '')
    model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
    
    if not api_key:
        return None, '未配置AI模型API Key，请在系统设置中配置'
    
    prompt = """请从以下内容中提取所有设备资产编号。

规则：
1. 资产编号格式类似: XACD-Z-001-001-001 或类似格式
2. 合并写法如 XACD-Z-001-001-001/003/007 需拆解为独立编号
3. 有些编号可能显示不全，尽量还原完整编号
4. 同时识别卡片编号
5. 返回JSON格式，包含两个数组:
{
  "asset_numbers": ["编号1", "编号2"],
  "card_numbers": ["卡片编号1"]
}

内容:
"""
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1"
        )
        
        messages_list = [
            {"role": "system", "content": "你是一个专业的数据解析助手，擅长从表格、图片等文档中提取设备资产编号信息。"},
            {"role": "user", "content": prompt + content}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages_list,
            temperature=0.1,
            max_tokens=2048
        )
        
        ai_content = response.choices[0].message.content
        
        # 解析JSON
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            data = json.loads(json_match.group())
            return data, None
        else:
            return None, 'AI返回格式异常'
            
    except Exception as e:
        return None, f'AI解析失败: {str(e)}'


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_ai_parse(request):
    """AI解析导入设备"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '')
        content_type = data.get('content_type', 'text')
        
        if not content:
            return JsonResponse({'success': False, 'message': '请提供解析内容'})
        
        result, error = parse_asset_numbers_with_ai(content, content_type)
        
        if error:
            return JsonResponse({'success': False, 'message': error})
        
        # 展开合并写法的编号
        all_asset_numbers = []
        for no in result.get('asset_numbers', []):
            expanded = expand_asset_no_pattern(no)
            all_asset_numbers.extend(expanded)
        
        all_card_numbers = result.get('card_numbers', [])
        
        # 查找匹配的设备
        found_devices = Device.objects.filter(
            Q(asset_no__in=all_asset_numbers) | Q(asset_card_no__in=all_card_numbers)
        ).exclude(status='scrapped').select_related('category', 'location', 'user')
        
        device_list = []
        for d in found_devices:
            device_list.append({
                'id': d.id,
                'asset_no': d.asset_no,
                'name': d.name,
                'model': d.model or '',
                'category': d.category.name if d.category else '',
                'location': d.location.get_full_path() if d.location else '',
                'user': d.user.realname if d.user else '',
            })
        
        # 未找到的编号
        found_asset_nos = set(found_devices.values_list('asset_no', flat=True))
        found_card_nos = set(found_devices.values_list('asset_card_no', flat=True))
        not_found = [no for no in all_asset_numbers if no not in found_asset_nos]
        not_found += [no for no in all_card_numbers if no not in found_card_nos]
        
        return JsonResponse({
            'success': True,
            'devices': device_list,
            'not_found': not_found,
            'parsed_count': len(all_asset_numbers) + len(all_card_numbers),
            'found_count': len(device_list),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_ai_parse_file(request):
    """AI解析文件（表格/图片）"""
    try:
        task_id = request.POST.get('task_id')
        file = request.FILES.get('file')
        
        if not file:
            return JsonResponse({'success': False, 'message': '请上传文件'})
        
        task = get_object_or_404(InventoryTask, pk=task_id)
        
        # 读取文件内容
        file_name = file.name.lower()
        content = ''
        
        if file_name.endswith(('.xlsx', '.xls')):
            # Excel文件
            import openpyxl
            from io import BytesIO
            
            wb = openpyxl.load_workbook(BytesIO(file.read()), data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                for row in ws.iter_rows(values_only=True):
                    row_text = ' '.join([str(cell) for cell in row if cell])
                    content += row_text + '\n'
                    
        elif file_name.endswith('.csv'):
            # CSV文件
            content = file.read().decode('utf-8', errors='ignore')
            
        elif file_name.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            # 图片 - 需要用base64编码传递给AI
            import base64
            image_data = base64.b64encode(file.read()).decode('utf-8')
            content = f"[图片数据: {file_name}]"
            # 对于图片，需要特殊处理，使用vision API
            return api_ai_parse_image(request, image_data, task)
            
        else:
            return JsonResponse({'success': False, 'message': '不支持的文件格式'})
        
        # 调用AI解析
        result, error = parse_asset_numbers_with_ai(content)
        
        if error:
            return JsonResponse({'success': False, 'message': error})
        
        return process_ai_parse_result(result, task, request.user)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def api_ai_parse_image(request, image_data, task):
    """使用Vision API解析图片"""
    api_key = get_config_value('llm_api_key', '')
    model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
    
    if not api_key:
        return JsonResponse({'success': False, 'message': '未配置AI模型API Key'})
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.xiaomimimo.com/v1"
        )
        
        prompt = """请从这张图片中提取所有设备资产编号。

规则：
1. 资产编号格式类似: XACD-Z-001-001-001
2. 合并写法如 XACD-Z-001-001-001/003/007 需拆解
3. 同时识别卡片编号
4. 返回JSON格式: {"asset_numbers": ["编号1"], "card_numbers": ["卡片编号1"]}"""
        
        messages_list = [
            {"role": "system", "content": "你是一个专业的数据解析助手，擅长从图片中提取设备资产编号。"},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages_list,
            temperature=0.1,
            max_tokens=2048
        )
        
        ai_content = response.choices[0].message.content
        
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            data = json.loads(json_match.group())
            return process_ai_parse_result(data, task, request.user)
        else:
            return JsonResponse({'success': False, 'message': 'AI返回格式异常'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'图片解析失败: {str(e)}'})


def process_ai_parse_result(result, task, user):
    """处理AI解析结果"""
    # 展开合并写法的编号
    all_asset_numbers = []
    for no in result.get('asset_numbers', []):
        expanded = expand_asset_no_pattern(no)
        all_asset_numbers.extend(expanded)
    
    all_card_numbers = result.get('card_numbers', [])
    
    # 查找匹配的设备
    found_devices = Device.objects.filter(
        Q(asset_no__in=all_asset_numbers) | Q(asset_card_no__in=all_card_numbers)
    ).exclude(status='scrapped').distinct()
    
    # 排除已添加的
    existing_ids = set(InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True))
    new_devices = [d for d in found_devices if d.id not in existing_ids]
    
    # 添加到任务
    current_max_order = InventoryTaskDevice.objects.filter(task=task).count()
    task_devices = []
    for i, device in enumerate(new_devices):
        task_devices.append(InventoryTaskDevice(
            task=task,
            device=device,
            status='pending',
            sort_order=current_max_order + i + 1,
            added_by=user,
        ))
    InventoryTaskDevice.objects.bulk_create(task_devices)
    
    # 更新计数
    task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
    task.save()
    
    # 未找到的编号
    found_asset_nos = set(found_devices.values_list('asset_no', flat=True))
    found_card_nos = set(found_devices.values_list('asset_card_no', flat=True))
    not_found = [no for no in all_asset_numbers if no not in found_asset_nos]
    
    return JsonResponse({
        'success': True,
        'message': f'已添加 {len(new_devices)} 台设备',
        'added_count': len(new_devices),
        'not_found': not_found,
        'parsed_count': len(all_asset_numbers),
        'total_count': task.device_count,
    })


# ==================== 新版导入设备 API ====================

def expand_asset_numbers_for_inventory(base_no, count):
    """展开合并写法的资产编号（与update_card_no相同）"""
    results = []
    
    # 处理 / 分隔的格式: XACD-Z-001-001-001/002/003
    slash_match = re.match(r'^(.+)-(\d+)/(.+)$', base_no)
    if slash_match:
        prefix = slash_match.group(1)
        first_num = slash_match.group(2)
        rest_nums = slash_match.group(3).split('/')
        results.append(f"{prefix}-{first_num}")
        for num in rest_nums:
            results.append(f"{prefix}-{num}")
        return results[:count] if count else results
    
    # 处理 ~ 连号格式: XACD-Z-001-001-006~009
    range_match = re.match(r'^(.+)-(\d+)~(\d+)$', base_no)
    if range_match:
        prefix = range_match.group(1)
        start = int(range_match.group(2))
        end = int(range_match.group(3))
        num_len = len(range_match.group(2))
        for i in range(start, end + 1):
            results.append(f"{prefix}-{str(i).zfill(num_len)}")
        return results[:count] if count else results
    
    # 普通格式，直接返回
    return [base_no]


def parse_inventory_excel(file_content):
    """解析Excel文件，返回资产编号和卡片编号的映射"""
    import openpyxl
    from io import BytesIO
    
    wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
    ws = wb.active
    
    # 1. 扫描前10行找到列名行（支持合并单元格）
    header_row = None
    asset_no_col = None
    card_no_col = None
    quantity_col = None
    
    merged_cells_map = {}
    for merged_range in ws.merged_cells.ranges:
        min_row = merged_range.min_row
        min_col = merged_range.min_col
        first_cell = ws.cell(row=min_row, column=min_col)
        first_value = str(first_cell.value).strip().lower() if first_cell.value else ''
        for row in range(min_row, min_row + (merged_range.max_row - merged_range.min_row + 1)):
            for col in range(min_col, min_col + (merged_range.max_col - merged_range.min_col + 1)):
                merged_cells_map[(row, col)] = (min_row, min_col, first_value)
    
    for row_idx in range(1, min(11, ws.max_row + 1)):
        row_values = []
        for col_idx in range(1, ws.max_column + 1):
            cell_value = ws.cell(row=row_idx, column=col_idx).value
            if (row_idx, col_idx) in merged_cells_map:
                _, _, merged_value = merged_cells_map[(row_idx, col_idx)]
                row_values.append(merged_value)
            else:
                row_values.append(str(cell_value).strip().lower() if cell_value else '')
        
        has_asset = any('资产编号' in v or '资产编码' in v for v in row_values)
        has_card = any('卡片编号' in v or '卡片码' in v for v in row_values)
        
        if has_asset and has_card:
            header_row = row_idx
            for idx, v in enumerate(row_values):
                if '资产编号' in v or '资产编码' in v:
                    asset_no_col = idx
                elif '卡片编号' in v or '卡片码' in v:
                    card_no_col = idx
                elif '数量' in v or '资产数量' in v:
                    quantity_col = idx
            break
    
    if asset_no_col is None or card_no_col is None:
        return None, '未找到资产编号列或卡片编号列'
    
    # 2. 从列名行下一行开始读取数据
    data_start_row = header_row + 1
    
    # 3. 构建映射
    excel_mappings = {}
    for row in ws.iter_rows(min_row=data_start_row, values_only=True):
        if len(row) > max(asset_no_col, card_no_col):
            asset_no = str(row[asset_no_col]).strip() if row[asset_no_col] else ''
            card_no = str(row[card_no_col]).strip() if row[card_no_col] else ''
            quantity = None
            if quantity_col is not None and quantity_col < len(row) and row[quantity_col]:
                try:
                    quantity = int(float(row[quantity_col]))
                except:
                    pass
            
            if asset_no:
                expanded = expand_asset_numbers_for_inventory(asset_no, quantity)
                for no in expanded:
                    excel_mappings[no] = card_no
    
    return excel_mappings, None


def parse_excel_with_ai_assist(file_content):
    """使用AI解析Excel/CSV内容（转为文本发送）"""
    import openpyxl
    from io import BytesIO
    import csv
    
    api_key = get_config_value('llm_api_key', '')
    model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
    
    if not api_key:
        return None, '未配置AI API Key'
    
    content_text = ''
    file_name = 'file.xlsx'
    
    if hasattr(file_content, 'name'):
        file_name = file_content.name.lower()
    elif isinstance(file_content, bytes):
        if file_content[:4] == b'%PDF':
            return None, '不支持PDF文件'
    
    if file_name.endswith('.csv'):
        if hasattr(file_content, 'read'):
            content = file_content.read().decode('utf-8')
        else:
            content = file_content.decode('utf-8')
        reader = csv.reader(content.splitlines())
        for row in reader:
            content_text += ' | '.join([str(cell) for cell in row if cell]) + '\n'
    else:
        wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        ws = wb.active
        for row in ws.iter_rows(max_row=50, values_only=True):
            content_text += ' | '.join([str(cell) if cell else '' for cell in row]) + '\n'
    
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.xiaomimimo.com/v1")
    
    prompt = f"""请从以下Excel/CSV表格数据中提取资产编号和卡片编号的对应关系。

规则：
1. 资产编号列可能包含：资产编号、资产编码
2. 卡片编号列可能包含：卡片编号、卡片码
3. 数量列可能包含：资产数量、数量
4. 资产编号可能包含合并写法如 XACD-Z-001-001-001/002/003，需要拆解
5. 连号写法如 006~009 也需要拆解
6. 返回JSON格式：
{{
  "mappings": [
    {{"asset_no": "XACD-Z-001-001-001", "card_no": "CARD-001"}},
    {{"asset_no": "XACD-Z-001-001-002", "card_no": "CARD-001"}}
  ]
}}

请直接分析数据内容，不要询问用户。

表格数据：
{content_text}"""
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的数据解析助手，擅长从表格数据中提取设备资产编号和卡片编号的对应关系。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096,
            temperature=0.1
        )
        
        ai_content = response.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        
        if json_match:
            return json.loads(json_match.group()), None
        return None, 'AI返回格式异常'
    except Exception as e:
        return None, f'AI解析失败: {str(e)}'


def call_ai_for_inventory_import(api_key, model_name, excel_data):
    """调用AI解析资产编号（与update_card_no相同）"""
    from openai import OpenAI
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.xiaomimimo.com/v1"
    )
    
    prompt = f"""请从以下Excel表格数据中提取资产编号和卡片编号的对应关系。

规则：
1. 自动识别包含"资产编号"、"卡片编号"、"资产数量"的列
2. 资产编号格式类似: XACD-Z-001-001-001
3. 合并写法如 XACD-Z-001-001-001/002/003 表示多个编号
4. 连号写法如 XACD-Z-001-001-006~009 表示连续编号
5. 结合资产数量字段判断拆解数量
6. 返回JSON格式，包含展开后的资产编号和对应卡片编号：
{{
  "mappings": [
    {{"asset_no": "XACD-Z-001-001-001", "card_no": "CARD-001"}},
    {{"asset_no": "XACD-Z-001-001-002", "card_no": "CARD-001"}},
    ...
  ]
}}

表格数据：
{excel_data}"""
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个专业的数据解析助手，擅长从表格数据中提取设备资产编号和卡片编号的对应关系。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4096,
            temperature=0.1
        )
        
        ai_content = response.choices[0].message.content
        
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        return None


def process_inventory_import_task(task_id, file_content, task, user, parse_photo_only):
    """后台处理导入任务"""
    from io import BytesIO
    import openpyxl
    
    progress = inventory_import_progress[task_id]
    
    try:
        file_name = 'unknown'
        if hasattr(file_content, 'name'):
            file_name = file_content.name.lower()
        elif isinstance(file_content, bytes):
            file_name = 'file.xlsx'
        
        # 判断文件类型
        if file_name.endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            # 图片文件 - 仅解析模式
            if parse_photo_only:
                inventory_add_log(task_id, 'info', '开始解析图片中的设备...')
                import base64
                image_data = base64.b64encode(file_content).decode('utf-8')
                
                # 调用AI解析图片
                api_key = get_config_value('llm_api_key', '')
                model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
                
                if not api_key:
                    progress['status'] = 'completed'
                    inventory_add_log(task_id, 'error', '未配置AI API Key')
                    return
                
                inventory_add_log(task_id, 'ai', f'调用AI Vision解析图片...')
                
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url="https://api.xiaomimimo.com/v1")
                
                prompt = """请从这张图片中提取所有设备资产编号和卡片编号。

规则：
1. 资产编号格式类似: XACD-Z-001-001-001
2. 合并写法如 XACD-Z-001-001-001/003/007 需拆解
3. 同时识别卡片编号
4. 返回JSON格式: {"asset_numbers": ["编号1"], "card_numbers": ["卡片编号1"]}"""
                
                messages = [
                    {"role": "system", "content": "你是一个专业的数据解析助手，擅长从图片中提取设备资产编号。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]}
                ]
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2048
                )
                
                ai_content = response.choices[0].message.content
                json_match = re.search(r'\{[\s\S]*\}', ai_content)
                
                if json_match:
                    data = json.loads(json_match.group())
                    asset_nos = data.get('asset_numbers', [])
                    card_nos = data.get('card_numbers', [])
                    
                    # 展开合并写法
                    all_asset_numbers = []
                    for no in asset_nos:
                        expanded = expand_asset_numbers_for_inventory(no, None)
                        all_asset_numbers.extend(expanded)
                    
                    inventory_add_log(task_id, 'success', f'AI解析成功，识别到 {len(all_asset_numbers)} 个资产编号')
                    
                    # 查找系统设备
                    found_devices = Device.objects.filter(
                        Q(asset_no__in=all_asset_numbers) | Q(asset_card_no__in=card_nos)
                    ).exclude(status='scrapped').select_related('category', 'location', 'user', 'department')
                    
                    progress['device_list'] = []
                    for d in found_devices:
                        progress['device_list'].append({
                            'id': d.id,
                            'asset_no': d.asset_no,
                            'asset_card_no': d.asset_card_no or '',
                            'name': d.name,
                            'category': d.category.name if d.category else '',
                            'location': d.location.get_full_path() if d.location else d.location_text or '',
                            'device_no': d.device_no or '',
                            'model': d.model or '',
                            'secret_level': d.get_secret_level_display(),
                            'department': d.department.name if d.department else '',
                            'user': d.user.realname if d.user else '',
                            'status': d.get_status_display(),
                            'is_fixed': d.is_fixed,
                        })
                    
                    inventory_add_log(task_id, 'success', f'在系统中找到 {len(progress["device_list"])} 台匹配设备')
                else:
                    inventory_add_log(task_id, 'error', 'AI返回格式异常，无法解析')
                
                progress['status'] = 'completed'
                return
            
            # 图片但不是仅解析模式 - 按Excel处理（一般不会走到这里）
            file_content = file_content.read() if hasattr(file_content, 'read') else file_content
        
        # Excel文件处理
        inventory_add_log(task_id, 'info', '开始读取Excel文件...')
        
        excel_mappings, error = parse_inventory_excel(file_content)
        
        if error:
            # 本地识别失败，尝试AI解析
            inventory_add_log(task_id, 'warning', f'本地解析失败: {error}，尝试AI解析...')
            
            ai_result, ai_error = parse_excel_with_ai_assist(file_content)
            
            if ai_error or not ai_result or 'mappings' not in ai_result:
                # AI也失败，返回需要手动选择
                progress['status'] = 'need_manual'
                progress['error'] = error
                progress['ai_error'] = ai_error
                inventory_add_log(task_id, 'error', f'本地和AI解析都失败: {ai_error or error}')
                return
            
            # 使用AI返回的映射数据
            ai_mappings = {item['asset_no']: item['card_no'] for item in ai_result['mappings']}
            inventory_add_log(task_id, 'success', f'AI解析成功，返回 {len(ai_mappings)} 条映射记录')
            excel_mappings = ai_mappings
        
        inventory_add_log(task_id, 'success', f'Excel文件读取成功，共 {len(excel_mappings)} 条资产编号映射')
        
        # 获取AI配置
        api_key = get_config_value('llm_api_key', '')
        model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
        
        # 如果有AI配置，使用AI解析
        if api_key:
            inventory_add_log(task_id, 'ai', f'调用AI解析数据，发送 {len(excel_mappings)} 条映射记录...')
            
            excel_text = '\n'.join([f"{k}|{v}" for k, v in excel_mappings.items()])
            ai_result = call_ai_for_inventory_import(api_key, model_name, excel_text)
            
            if ai_result and 'mappings' in ai_result:
                ai_mappings = {item['asset_no']: item['card_no'] for item in ai_result['mappings']}
                inventory_add_log(task_id, 'success', f'AI解析成功，返回 {len(ai_mappings)} 条映射记录')
                excel_mappings = ai_mappings
            else:
                inventory_add_log(task_id, 'warning', 'AI解析失败或返回格式错误，使用本地解析结果')
        
        # 获取任务中已存在的设备
        existing_device_ids = set(InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True))
        
        # 遍历系统设备进行匹配
        inventory_add_log(task_id, 'info', '开始匹配系统设备...')
        
        all_devices = Device.objects.exclude(status='scrapped').select_related('category', 'location', 'user', 'department')
        total = all_devices.count()
        progress['total'] = total
        
        added_count = 0
        skipped_count = 0
        not_found = []
        
        for device in all_devices:
            progress['current'] += 1
            
            if device.asset_no in excel_mappings:
                # 匹配成功
                if device.id in existing_device_ids:
                    # 已在任务中
                    skipped_count += 1
                    inventory_add_log(task_id, 'warning', f'设备 {device.asset_no}：已在任务中，跳过')
                else:
                    # 添加到任务
                    InventoryTaskDevice.objects.create(
                        task=task,
                        device=device,
                        status='pending',
                        sort_order=progress['current'],
                        added_by=user,
                    )
                    added_count += 1
                    inventory_add_log(task_id, 'success', f'设备 {device.asset_no}：匹配成功，已添加到任务')
            else:
                # 未匹配
                not_found.append(device.asset_no)
            
            if progress['current'] % 10 == 0:
                time.sleep(0.05)
        
        # 更新任务设备计数
        task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
        task.save()
        
        progress['added_count'] = added_count
        progress['skipped_count'] = skipped_count
        progress['not_found'] = not_found[:100]  # 限制返回数量
        
        progress['status'] = 'completed'
        inventory_add_log(task_id, 'success', f'处理完成！共处理 {total} 个设备，已添加 {added_count} 个，已存在 {skipped_count} 个')
        
    except Exception as e:
        progress['status'] = 'completed'
        progress['errors'].append(str(e))
        inventory_add_log(task_id, 'error', f'处理失败: {str(e)}')


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_import_devices(request, task_id):
    """导入设备API"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'success': False, 'message': '请上传文件'})
    
    parse_photo_only = request.POST.get('parse_photo_only', 'false').lower() == 'true'
    
    # 如果是图片且选择仅解析模式
    file_name = file.name.lower()
    is_image = file_name.endswith(('.png', '.jpg', '.jpeg', '.bmp'))
    
    if is_image and parse_photo_only:
        # 图片解析模式 - 同步处理，返回设备列表
        return handle_image_parse_only(task, file, request.user)
    
    # Excel导入模式 - 后台异步处理
    task_id_str = str(uuid.uuid4())[:8]
    file_content = file.read()
    
    inventory_import_progress[task_id_str] = {
        'status': 'processing',
        'total': 0,
        'current': 0,
        'added_count': 0,
        'skipped_count': 0,
        'errors': [],
        'not_found': [],
        'logs': [],
        'device_list': None,
        'file_content': file_content,
    }
    
    thread = threading.Thread(
        target=process_inventory_import_task,
        args=(task_id_str, file_content, task, request.user, parse_photo_only)
    )
    thread.daemon = True
    thread.start()
    
    return JsonResponse({'success': True, 'task_id': task_id_str})


def handle_image_parse_only(task, file, user):
    """处理图片仅解析模式"""
    import base64
    from openai import OpenAI
    
    api_key = get_config_value('llm_api_key', '')
    model_name = get_config_value('llm_model_name', 'mimo-v2-pro')
    
    if not api_key:
        return JsonResponse({'success': False, 'message': '未配置AI API Key'})
    
    try:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        
        client = OpenAI(api_key=api_key, base_url="https://api.xiaomimimo.com/v1")
        
        prompt = """请从这张图片中提取所有设备资产编号和卡片编号。

规则：
1. 资产编号格式类似: XACD-Z-001-001-001
2. 合并写法如 XACD-Z-001-001-001/003/007 需拆解
3. 同时识别卡片编号
4. 返回JSON格式: {"asset_numbers": ["编号1"], "card_numbers": ["卡片编号1"]}"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的数据解析助手，擅长从图片中提取设备资产编号。"},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
            ]}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )
        
        ai_content = response.choices[0].message.content
        json_match = re.search(r'\{[\s\S]*\}', ai_content)
        
        if not json_match:
            return JsonResponse({'success': False, 'message': 'AI返回格式异常'})
        
        data = json.loads(json_match.group())
        asset_nos = data.get('asset_numbers', [])
        card_nos = data.get('card_numbers', [])
        
        # 展开合并写法
        all_asset_numbers = []
        for no in asset_nos:
            expanded = expand_asset_numbers_for_inventory(no, None)
            all_asset_numbers.extend(expanded)
        
        # 查找系统设备
        found_devices = Device.objects.filter(
            Q(asset_no__in=all_asset_numbers) | Q(asset_card_no__in=card_nos)
        ).exclude(status='scrapped').select_related('category', 'location', 'user', 'department')
        
        # 获取已存在的设备
        existing_ids = set(InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True))
        
        device_list = []
        for d in found_devices:
            if d.id not in existing_ids:
                device_list.append({
                    'id': d.id,
                    'asset_no': d.asset_no,
                    'asset_card_no': d.asset_card_no or '',
                    'name': d.name,
                    'category': d.category.name if d.category else '',
                    'location': d.location.get_full_path() if d.location else d.location_text or '',
                    'device_no': d.device_no or '',
                    'model': d.model or '',
                    'secret_level': d.get_secret_level_display(),
                    'department': d.department.name if d.department else '',
                    'user': d.user.realname if d.user else '',
                    'status': d.get_status_display(),
                    'is_fixed': d.is_fixed,
                })
        
        return JsonResponse({
            'success': True,
            'device_list': device_list,
            'parsed_count': len(all_asset_numbers),
            'found_count': len(device_list),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'图片解析失败: {str(e)}'})


@login_required
def api_import_progress(request, task_id):
    """导入进度查询API"""
    task_id_str = request.GET.get('task_id')
    if task_id_str and task_id_str in inventory_import_progress:
        data = inventory_import_progress[task_id_str].copy()
        # 排除无法序列化的字段
        data.pop('file_content', None)
        return JsonResponse(data)
    return JsonResponse({'status': 'not_found'})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_manual_parse_excel(request, task_id):
    """手动指定列解析Excel"""
    import base64
    import openpyxl
    from io import BytesIO
    
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        
        task_id_str = data.get('task_id')
        asset_col = int(data.get('asset_col', 0))
        card_col = int(data.get('card_col', 1))
        qty_col = data.get('qty_col')
        if qty_col is not None:
            qty_col = int(qty_col)
            if qty_col < 0:
                qty_col = None
        
        if task_id_str and task_id_str in inventory_import_progress:
            progress = inventory_import_progress[task_id_str]
            file_content = progress.get('file_content')
        else:
            return JsonResponse({'success': False, 'message': '任务已过期，请重新上传文件'})
        
        if not file_content:
            return JsonResponse({'success': False, 'message': '文件内容丢失'})
        
        inventory_add_log(task_id_str, 'info', '手动解析：开始解析Excel...')
        
        wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
        ws = wb.active
        
        excel_mappings = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) > max(asset_col, card_col):
                asset_no = str(row[asset_col]).strip() if row[asset_col] else ''
                card_no = str(row[card_col]).strip() if row[card_col] else ''
                quantity = None
                if qty_col is not None and qty_col < len(row) and row[qty_col]:
                    try:
                        quantity = int(float(row[qty_col]))
                    except:
                        pass
                
                if asset_no:
                    expanded = expand_asset_numbers_for_inventory(asset_no, quantity)
                    for no in expanded:
                        excel_mappings[no] = card_no
        
        inventory_add_log(task_id_str, 'success', f'手动解析成功，共 {len(excel_mappings)} 条资产编号映射')
        
        existing_device_ids = set(InventoryTaskDevice.objects.filter(task=task).values_list('device_id', flat=True))
        
        all_devices = Device.objects.exclude(status='scrapped').select_related('category', 'location', 'user', 'department')
        total = all_devices.count()
        
        added_count = 0
        skipped_count = 0
        not_found = []
        
        for device in all_devices:
            if device.asset_no in excel_mappings:
                if device.id in existing_device_ids:
                    skipped_count += 1
                    inventory_add_log(task_id_str, 'warning', f'设备 {device.asset_no}：已在任务中，跳过')
                else:
                    InventoryTaskDevice.objects.create(
                        task=task,
                        device=device,
                        status='pending',
                        sort_order=added_count + skipped_count + 1,
                        added_by=request.user,
                    )
                    added_count += 1
                    inventory_add_log(task_id_str, 'success', f'设备 {device.asset_no}：匹配成功，已添加到任务')
            else:
                not_found.append(device.asset_no)
        
        task.device_count = InventoryTaskDevice.objects.filter(task=task).count()
        task.save()
        
        inventory_add_log(task_id_str, 'success', f'处理完成！已添加 {added_count} 个，已存在 {skipped_count} 个')
        
        return JsonResponse({
            'success': True,
            'added_count': added_count,
            'skipped_count': skipped_count,
            'not_found_count': len(not_found[:100]),
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'解析失败: {str(e)}'})


# ==================== 盘点执行 ====================

@login_required
def task_execute(request, pk):
    """盘点执行页面"""
    task = get_object_or_404(InventoryTask.objects.select_related('created_by', 'assignee'), pk=pk)
    
    # 待盘点设备 - 有位置的在前，无位置的在后，按位置排序
    pending_devices = InventoryTaskDevice.objects.filter(
        task=task, status='pending'
    ).select_related(
        'device__category', 'device__location', 'device__user', 'device__department', 'device__workstation'
    ).annotate(
        has_location=Case(
            When(device__location_text='', then=1),
            default=0,
            output_field=IntegerField(),
        )
    ).order_by('has_location', 'device__location_text', 'device__id')
    
    # 已盘点设备 - 按盘点时间倒序，新盘点的在前
    checked_devices = InventoryTaskDevice.objects.filter(
        task=task, status='checked'
    ).select_related(
        'device__category', 'device__location', 'device__user', 'device__department', 'device__workstation'
    ).order_by('-checked_at')
    
    # 统计
    total_count = InventoryTaskDevice.objects.filter(task=task).count()
    pending_count = pending_devices.count()
    checked_count = total_count - pending_count
    
    # 获取位置树（用于地图选位）
    from apps.assets.views import get_location_tree_data
    location_tree = get_location_tree_data()
    
    # 获取部门和用户列表（用于分配）
    departments = Department.objects.all()
    
    return render(request, 'inventory/task_execute.html', {
        'task': task,
        'pending_devices': pending_devices,
        'checked_devices': checked_devices,
        'total_count': total_count,
        'pending_count': pending_count,
        'checked_count': checked_count,
        'location_tree': json.dumps(location_tree),
        'departments': departments,
    })


@login_required
def api_device_detail(request, task_id, device_id):
    """获取设备详情（盘点时展示）"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    device = get_object_or_404(
        Device.objects.select_related('category', 'location', 'user', 'department', 'workstation'),
        pk=device_id
    )
    
    data = {
        'id': device.id,
        'asset_no': device.asset_no,
        'device_no': device.device_no or '',
        'name': device.name,
        'model': device.model or '',
        'serial_no': device.serial_no or '',
        'brand': device.brand or '',
        'category': device.category.name if device.category else '',
        'category_id': device.category_id,
        'secret_level': device.get_secret_level_display(),
        'status': device.get_status_display(),
        'status_code': device.status,
        
        # 使用信息
        'department': device.department.name if device.department else '',
        'department_id': device.department_id,
        'user': device.user.realname if device.user else '',
        'user_id': device.user_id,
        'location': device.location.get_full_path() if device.location else '',
        'location_id': device.location_id,
        'workstation': device.workstation.workstation_code if device.workstation else '',
        'workstation_id': device.workstation_id,
        
        # 网络信息
        'mac_address': device.mac_address or '',
        'ip_address': device.ip_address or '',
        
        # 设备信息
        'os_name': device.os_name or '',
        'disk_serial': device.disk_serial or '',
        'purchase_date': str(device.purchase_date) if device.purchase_date else '',
        'enable_date': str(device.enable_date) if device.enable_date else '',
        'install_date': str(device.install_date) if device.install_date else '',
        
        # 其他信息
        'is_fixed': device.is_fixed,
        'asset_card_no': device.asset_card_no or '',
        'is_secret': device.is_secret,
        'secret_category': device.secret_category or '',
        'purpose': device.purpose or '',
        'remarks': device.remarks or '',
        
        # 照片
        'photo_url': device.photo.url if device.photo else '',
        'photo_updated_at': str(device.photo_updated_at) if device.photo_updated_at else '',
    }
    
    # 如果设备有关联工位，获取地图信息
    ws_location_id = None
    if device.workstation_id:
        ws_location_id = device.workstation.location_id
    elif device.location_id:
        loc = device.location
        while loc and loc.level != 3:
            loc = loc.parent
        if loc:
            ws_location_id = loc.id
    
    data['map_location_id'] = ws_location_id
    
    return JsonResponse({'success': True, 'device': data})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_check_device(request, task_id):
    """确认盘点设备"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        # 支持JSON和FormData两种格式
        if request.content_type and 'multipart/form-data' in request.content_type:
            # FormData格式（支持文件上传）
            task_device_id = request.POST.get('task_device_id')
            device_id = request.POST.get('device_id')
            location_status = request.POST.get('location_status', 'in_place')
            asset_status = request.POST.get('asset_status', 'normal')
            remarks = request.POST.get('remarks', '')
            source = request.POST.get('source', 'manual')
            photo_file = request.FILES.get('photo')
        else:
            # JSON格式
            data = json.loads(request.body)
            task_device_id = data.get('task_device_id')
            device_id = data.get('device_id')
            location_status = data.get('location_status', 'in_place')
            asset_status = data.get('asset_status', 'normal')
            remarks = data.get('remarks', '')
            source = data.get('source', 'manual')
            photo_file = None
        
        task_device = get_object_or_404(InventoryTaskDevice, pk=task_device_id, task=task)
        device = task_device.device
        
        # 如果有照片，上传并更新设备照片
        if photo_file:
            save_photo_with_asset_no(device, photo_file)
            device.photo_updated_at = timezone.now()
            device.save(update_fields=['photo', 'photo_updated_at'])
        
        # 创建盘点记录
        record = InventoryRecord.objects.create(
            task=task,
            device=device,
            task_device=task_device,
            device_status=device.status,
            location_status=location_status,
            asset_status=asset_status,
            remarks=remarks,
            checked_by=request.user,
            source=source,
        )
        
        # 如果有备注，更新设备备注字段
        if remarks:
            device.remarks = remarks
            device.save(update_fields=['remarks'])
        
        # 更新任务设备状态
        task_device.status = 'checked'
        task_device.checked_at = timezone.now()
        task_device.save()
        
        # 更新任务计数
        task.checked_count = InventoryTaskDevice.objects.filter(task=task, status='checked').count()
        task.save()
        
        # 如果设备未找到，更新设备状态
        if location_status == 'not_found':
            device.status = 'fault'
            device.fault_reason = '盘点未找到'
            device.save()
        
        return JsonResponse({
            'success': True,
            'message': f'设备 {device.asset_no} 盘点完成',
            'checked_count': task.checked_count,
            'pending_count': InventoryTaskDevice.objects.filter(task=task, status='pending').count(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_scan_check(request, task_id):
    """扫码盘点"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        qrcode_content = data.get('qrcode', '')
        
        # 解析二维码URL，提取资产编号
        # 格式如: https://itams.chidafeiji.com/assets/view/XACD-Z-001-001-001/
        asset_no = None
        
        if '/assets/view/' in qrcode_content:
            # 提取资产编号
            match = re.search(r'/assets/view/([^/]+)', qrcode_content)
            if match:
                asset_no = match.group(1)
        elif '/device/scan/' in qrcode_content:
            # 兼容旧格式
            match = re.search(r'/device/scan/(\d+)', qrcode_content)
            if match:
                device_id = match.group(1)
                device = Device.objects.filter(id=device_id).first()
                if device:
                    asset_no = device.asset_no
        
        if not asset_no:
            return JsonResponse({'success': False, 'message': '无法解析二维码内容'})
        
        # 查找设备
        device = Device.objects.filter(asset_no=asset_no).exclude(status='scrapped').first()
        if not device:
            return JsonResponse({'success': False, 'message': f'未找到设备: {asset_no}'})
        
        # 查找任务设备
        task_device = InventoryTaskDevice.objects.filter(
            task=task, device=device, status='pending'
        ).first()
        
        if not task_device:
            return JsonResponse({
                'success': False,
                'message': f'设备 {asset_no} 不在待盘点列表中',
                'device_not_in_task': True,
                'device_id': device.id,
                'asset_no': asset_no,
            })
        
        # 返回设备信息，准备盘点
        return JsonResponse({
            'success': True,
            'message': f'已找到设备: {asset_no}',
            'task_device_id': task_device.id,
            'device_id': device.id,
            'asset_no': device.asset_no,
            'name': device.name,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_update_device_info(request, task_id):
    """更新设备信息（分配、位置）"""
    task = get_object_or_404(InventoryTask, pk=task_id)
    
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        update_type = data.get('update_type')  # 'assign' 或 'location'
        
        device = get_object_or_404(Device, pk=device_id)
        
        if update_type == 'assign':
            # 更新部门和使用人
            user_id = data.get('user_id')
            department_id = data.get('department_id')
            
            old_dept = device.department.name if device.department else ''
            old_user = device.user.realname if device.user else ''
            
            # 如果传入了user_id，自动获取用户的部门
            if user_id:
                user_obj = User.objects.filter(pk=user_id).first()
                if user_obj:
                    device.user_id = user_id
                    device.department_id = user_obj.department_id  # 自动同步用户所属部门
                    device.status = 'normal'
                else:
                    device.user_id = user_id
                    device.department_id = department_id if department_id else None
                    device.status = 'normal'
            else:
                device.user_id = None
                device.department_id = department_id if department_id else None
                device.status = 'unused'
            
            device.save()
            
            from apps.assets.models import AssetLog
            AssetLog.objects.create(
                device=device,
                user=request.user,
                action='assign',
                field_name='user',
                old_value=f'{old_dept}/{old_user}',
                new_value=f'{device.department.name if device.department else ""}/{device.user.realname if device.user else ""}',
                remarks='盘点时更新'
            )
            
            return JsonResponse({
                'success': True,
                'message': '分配信息已更新',
                'department': device.department.name if device.department else '',
                'user': device.user.realname if device.user else '',
            })
            
        elif update_type == 'location':
            # 更新位置和工位
            location_id = data.get('location_id')
            workstation_id = data.get('workstation_id')
            
            old_location = device.location.get_full_path() if device.location else ''
            old_ws = device.workstation.workstation_code if device.workstation else ''
            old_ws_id = device.workstation_id
            
            device.location_id = location_id if location_id else None
            device.workstation_id = workstation_id if workstation_id else None
            
            # 根据工位更新位置
            if workstation_id:
                ws = device.workstation
                if ws.area_id:
                    device.location_id = ws.area_id
                else:
                    device.location_id = ws.location_id
                ws.status = 'occupied'
                ws.save()
            
            device.save()
            
            # 释放旧工位
            if old_ws_id and old_ws_id != workstation_id:
                from apps.assets.models import Workstation
                old_ws_obj = Workstation.objects.filter(id=old_ws_id).first()
                if old_ws_obj and not old_ws_obj.devices.exists():
                    old_ws_obj.status = 'available'
                    old_ws_obj.save()
            
            from apps.assets.models import AssetLog
            AssetLog.objects.create(
                device=device,
                user=request.user,
                action='transfer',
                field_name='location',
                old_value=f'{old_location}/{old_ws}',
                new_value=f'{device.location.get_full_path() if device.location else ""}/{device.workstation.workstation_code if device.workstation else ""}',
                remarks='盘点时更新'
            )
            
            return JsonResponse({
                'success': True,
                'message': '位置信息已更新',
                'location': device.location.get_full_path() if device.location else '',
                'workstation': device.workstation.workstation_code if device.workstation else '',
            })
        
        else:
            return JsonResponse({'success': False, 'message': '无效的更新类型'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# ==================== 辅助函数 ====================

def generate_task_devices(task):
    """生成任务设备列表（全盘/动态盘点）"""
    devices = Device.objects.exclude(status='scrapped')
    
    if task.is_fixed_only:
        devices = devices.filter(is_fixed=True)
    
    # 按位置排序，无位置的按ID排序
    devices = devices.order_by('location_text', 'id')
    
    task_devices = []
    for i, device in enumerate(devices):
        task_devices.append(InventoryTaskDevice(
            task=task,
            device=device,
            status='pending',
            sort_order=i + 1,
            added_by=task.created_by,
        ))
    
    InventoryTaskDevice.objects.bulk_create(task_devices)
    
    task.device_count = len(task_devices)
    task.save()


# ==================== 兼容旧接口 ====================

@login_required
def plan_list(request):
    """盘点计划列表（兼容）"""
    plans = InventoryPlan.objects.all()
    return render(request, 'inventory/plan_list.html', {'plans': plans})


@login_required
def plan_create(request):
    """创建盘点计划（兼容）"""
    if request.method == 'POST':
        plan = InventoryPlan.objects.create(
            name=request.POST.get('name'),
            plan_type=request.POST.get('plan_type'),
            scope=request.POST.get('scope'),
            location_ids=request.POST.get('location_ids', ''),
            category_ids=request.POST.get('category_ids', ''),
            scheduled_start=request.POST.get('scheduled_start'),
            scheduled_end=request.POST.get('scheduled_end'),
            creator=request.user,
            remarks=request.POST.get('remarks'),
        )
        messages.success(request, f'盘点计划创建成功: {plan.plan_no}')
        return redirect('plan_list')
    
    locations = AssetLocation.objects.all()
    categories = AssetCategory.objects.all()
    return render(request, 'inventory/plan_form.html', {'locations': locations, 'categories': categories})


@login_required
def plan_detail(request, pk):
    """盘点计划详情（兼容）"""
    plan = get_object_or_404(InventoryPlan, pk=pk)
    tasks = plan.tasks.all()
    return render(request, 'inventory/plan_detail.html', {'plan': plan, 'tasks': tasks})


@login_required
def inventory_report(request):
    """盘点报表"""
    plans = InventoryPlan.objects.all()
    tasks = InventoryTask.objects.all()
    
    total_plans = plans.count()
    completed_plans = plans.filter(status='completed').count()
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    
    total_records = InventoryRecord.objects.count()
    not_found_count = InventoryRecord.objects.filter(location_status='not_found').count()
    damaged_count = InventoryRecord.objects.filter(asset_status='damaged').count()
    
    context = {
        'total_plans': total_plans,
        'completed_plans': completed_plans,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'total_records': total_records,
        'not_found_count': not_found_count,
        'damaged_count': damaged_count,
    }
    
    return render(request, 'inventory/report.html', context)


# ==================== 兼容旧接口 - 盘点审核 ====================

@login_required
def task_verify(request, pk):
    """盘点审核（兼容旧接口）"""
    task = get_object_or_404(InventoryTask, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()
            messages.success(request, '盘点任务审核通过')
        elif action == 'difference':
            record_id = request.POST.get('record_id')
            diff_action = request.POST.get('diff_action')
            diff_remarks = request.POST.get('diff_remarks', '')
            
            record = get_object_or_404(InventoryRecord, pk=record_id)
            
            if diff_action == 'profit':
                messages.success(request, '已确认为盘盈')
            elif diff_action == 'loss':
                messages.success(request, '已确认为盘亏')
            elif diff_action == 'damage':
                record.asset_status = 'damaged'
                record.remarks = diff_remarks
                record.save()
                messages.success(request, '已确认为损毁')
        
        return redirect('task_verify', pk)
    
    records = task.records.select_related('device', 'checked_by').all()
    
    in_place = records.filter(location_status='in_place').count()
    moved = records.filter(location_status='moved').count()
    not_found = records.filter(location_status='not_found').count()
    normal = records.filter(asset_status='normal').count()
    damaged = records.filter(asset_status='damaged').count()
    lost = records.filter(asset_status='lost').count()
    
    stats = {
        'total': task.device_count,
        'checked': task.checked_count,
        'in_place': in_place,
        'moved': moved,
        'not_found': not_found,
        'normal': normal,
        'damaged': damaged,
        'lost': lost,
    }
    
    return render(request, 'inventory/task_verify.html', {'task': task, 'records': records, 'stats': stats})
