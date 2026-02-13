from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import SystemLog, SystemAssetLog


@login_required
def login_log_list(request):
    search = request.GET.get('search', '')
    log_type = request.GET.get('type', '')
    
    logs = SystemLog.objects.select_related('user').all()
    
    if search:
        logs = logs.filter(Q(username__icontains=search) | Q(ip_address__icontains=search))
    if log_type:
        logs = logs.filter(log_type=log_type)
    
    paginator = Paginator(logs, 30)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    return render(request, 'logs/login_log_list.html', {'logs': logs})


@login_required
def operation_log_list(request):
    search = request.GET.get('search', '')
    module = request.GET.get('module', '')
    
    logs = SystemLog.objects.select_related('user').filter(log_type='operation')
    
    if search:
        logs = logs.filter(Q(action__icontains=search) | Q(username__icontains=search))
    if module:
        logs = logs.filter(module=module)
    
    paginator = Paginator(logs, 30)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    return render(request, 'logs/operation_log_list.html', {'logs': logs})


@login_required
def asset_log_list(request):
    search = request.GET.get('search', '')
    action = request.GET.get('action', '')
    
    logs = SystemAssetLog.objects.select_related('device', 'user').all()
    
    if search:
        logs = logs.filter(Q(device__asset_no__icontains=search) | Q(device__name__icontains=search))
    if action:
        logs = logs.filter(action=action)
    
    paginator = Paginator(logs, 30)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    
    return render(request, 'logs/asset_log_list.html', {'logs': logs})
