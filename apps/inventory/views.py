from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from .models import InventoryPlan, InventoryTask, InventoryRecord
from apps.assets.models import Device, AssetLocation, AssetCategory


@login_required
def plan_list(request):
    plans = InventoryPlan.objects.all()
    return render(request, 'inventory/plan_list.html', {'plans': plans})


@login_required
def plan_create(request):
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
def plan_edit(request, pk):
    plan = get_object_or_404(InventoryPlan, pk=pk)
    
    if request.method == 'POST':
        plan.name = request.POST.get('name')
        plan.plan_type = request.POST.get('plan_type')
        plan.scope = request.POST.get('scope')
        plan.location_ids = request.POST.get('location_ids', '')
        plan.category_ids = request.POST.get('category_ids', '')
        plan.scheduled_start = request.POST.get('scheduled_start')
        plan.scheduled_end = request.POST.get('scheduled_end')
        plan.remarks = request.POST.get('remarks')
        plan.save()
        messages.success(request, '盘点计划更新成功')
        return redirect('plan_list')
    
    locations = AssetLocation.objects.all()
    categories = AssetCategory.objects.all()
    return render(request, 'inventory/plan_form.html', {'plan': plan, 'locations': locations, 'categories': categories})


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(InventoryPlan, pk=pk)
    tasks = plan.tasks.all()
    return render(request, 'inventory/plan_detail.html', {'plan': plan, 'tasks': tasks})


@login_required
def plan_delete(request, pk):
    if request.method == 'POST':
        plan = get_object_or_404(InventoryPlan, pk=pk)
        if plan.status != 'draft':
            messages.error(request, '只能删除草稿状态的盘点计划')
        else:
            plan.delete()
            messages.success(request, '盘点计划删除成功')
    return redirect('plan_list')


@login_required
def plan_generate_tasks(request, pk):
    plan = get_object_or_404(InventoryPlan, pk=pk)
    
    if plan.status != 'draft':
        messages.error(request, '只能为草稿状态的计划生成任务')
        return redirect('plan_detail', pk)
    
    location_ids = [int(i) for i in plan.location_ids.split(',') if i]
    category_ids = [int(i) for i in plan.category_ids.split(',') if i]
    
    devices = Device.objects.all()
    if location_ids:
        devices = devices.filter(location_id__in=location_ids)
    if category_ids:
        devices = devices.filter(category_id__in=category_ids)
    
    if location_ids:
        for loc_id in location_ids:
            location = AssetLocation.objects.get(pk=loc_id)
            task = InventoryTask.objects.create(
                plan=plan,
                location=location,
                device_count=devices.filter(location=location).count(),
            )
    else:
        InventoryTask.objects.create(
            plan=plan,
            device_count=devices.count(),
        )
    
    plan.status = 'pending'
    plan.save()
    messages.success(request, '盘点任务已生成')
    return redirect('plan_detail', pk)


@login_required
def plan_start(request, pk):
    plan = get_object_or_404(InventoryPlan, pk=pk)
    plan.status = 'in_progress'
    plan.actual_start = timezone.now()
    plan.save()
    messages.success(request, '盘点计划已开始')
    return redirect('plan_detail', pk)


@login_required
def plan_complete(request, pk):
    plan = get_object_or_404(InventoryPlan, pk=pk)
    plan.status = 'completed'
    plan.actual_end = timezone.now()
    plan.save()
    messages.success(request, '盘点计划已完成')
    return redirect('plan_detail', pk)


@login_required
def task_list(request):
    status = request.GET.get('status', '')
    tasks = InventoryTask.objects.select_related('plan', 'location', 'assignee').all()
    if status:
        tasks = tasks.filter(status=status)
    return render(request, 'inventory/task_list.html', {'tasks': tasks})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(InventoryTask.objects.select_related('plan', 'location', 'category', 'assignee'), pk=pk)
    records = task.records.select_related('device', 'checked_by').all()
    return render(request, 'inventory/task_detail.html', {'task': task, 'records': records})


@login_required
def task_execute(request, pk):
    task = get_object_or_404(InventoryTask, pk=pk)
    
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        location_status = request.POST.get('location_status')
        asset_status = request.POST.get('asset_status', 'normal')
        remarks = request.POST.get('remarks', '')
        
        device = Device.objects.get(pk=device_id)
        
        InventoryRecord.objects.create(
            task=task,
            device=device,
            device_status=device.status,
            location_status=location_status,
            asset_status=asset_status,
            remarks=remarks,
            checked_by=request.user,
            source='manual',
        )
        
        task.checked_count += 1
        if location_status == 'not_found':
            device.status = 'fault'
            device.save()
        task.save()
        
        messages.success(request, f'设备 {device.asset_no} 盘点成功')
        return redirect('task_execute', pk)
    
    devices = Device.objects.all()
    if task.location:
        devices = devices.filter(location=task.location)
    if task.category:
        devices = devices.filter(category=task.category)
    
    checked_ids = task.records.values_list('device_id', flat=True)
    unchecked_devices = devices.exclude(id__in=checked_ids)
    
    return render(request, 'inventory/task_execute.html', {
        'task': task,
        'devices': unchecked_devices[:20],
    })


@login_required
def task_assign(request, pk):
    task = get_object_or_404(InventoryTask, pk=pk)
    if request.method == 'POST':
        from apps.accounts.models import User
        task.assignee_id = request.POST.get('assignee_id')
        task.status = 'pending'
        task.save()
        messages.success(request, '任务分配成功')
    return redirect('task_detail', pk)


@login_required
def api_scan_device(request):
    qrcode_data = request.GET.get('qrcode', '')
    if qrcode_data.startswith('/device/scan/'):
        device_id = qrcode_data.split('/')[-1]
        try:
            device = Device.objects.get(pk=device_id)
            return JsonResponse({
                'success': True,
                'device': {
                    'id': device.id,
                    'asset_no': device.asset_no,
                    'name': device.name,
                    'category': str(device.category),
                    'location': str(device.location) if device.location else '',
                    'user': str(device.user) if device.user else '',
                }
            })
        except Device.DoesNotExist:
            return JsonResponse({'success': False, 'message': '设备不存在'})
    return JsonResponse({'success': False, 'message': '无效的二维码'})


@login_required
def api_record_device(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        task_id = data.get('task_id')
        device_id = data.get('device_id')
        location_status = data.get('location_status')
        asset_status = data.get('asset_status', 'normal')
        remarks = data.get('remarks', '')
        
        task = InventoryTask.objects.get(pk=task_id)
        device = Device.objects.get(pk=device_id)
        
        InventoryRecord.objects.create(
            task=task,
            device=device,
            device_status=device.status,
            location_status=location_status,
            asset_status=asset_status,
            remarks=remarks,
            checked_by=request.user,
            source='wechat',
        )
        
        task.checked_count += 1
        task.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
def task_verify(request, pk):
    task = get_object_or_404(InventoryTask, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        record_id = request.POST.get('record_id')
        
        if action == 'confirm':
            task.status = 'verified'
            task.completed_at = timezone.now()
            task.save()
            messages.success(request, '盘点任务审核通过')
        elif action == 'difference':
            record = get_object_or_404(InventoryRecord, pk=record_id)
            diff_action = request.POST.get('diff_action')
            diff_remarks = request.POST.get('diff_remarks', '')
            
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


@login_required
def inventory_report(request):
    plans = InventoryPlan.objects.all()
    
    total_plans = plans.count()
    completed_plans = plans.filter(status='completed').count()
    in_progress_plans = plans.filter(status='in_progress').count()
    
    tasks = InventoryTask.objects.all()
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()
    verified_tasks = tasks.filter(status='verified').count()
    
    total_devices = Device.objects.count()
    total_records = InventoryRecord.objects.count()
    
    not_found_count = InventoryRecord.objects.filter(location_status='not_found').count()
    damaged_count = InventoryRecord.objects.filter(asset_status='damaged').count()
    lost_count = InventoryRecord.objects.filter(asset_status='lost').count()
    
    context = {
        'total_plans': total_plans,
        'completed_plans': completed_plans,
        'in_progress_plans': in_progress_plans,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'verified_tasks': verified_tasks,
        'total_devices': total_devices,
        'total_records': total_records,
        'not_found_count': not_found_count,
        'damaged_count': damaged_count,
        'lost_count': lost_count,
    }
    
    return render(request, 'inventory/report.html', context)
