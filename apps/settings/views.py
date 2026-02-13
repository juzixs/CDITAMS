from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse
from django.conf import settings
import os
import shutil
import sqlite3
from datetime import datetime
from .models import SystemConfig, Organization


@login_required
def config_list(request):
    group = request.GET.get('group', '')
    configs = SystemConfig.objects.all()
    if group:
        configs = configs.filter(config_group=group)
    return render(request, 'settings/config_list.html', {'configs': configs})


@login_required
def config_edit(request, pk):
    config = get_object_or_404(SystemConfig, pk=pk)
    
    if request.method == 'POST':
        if config.is_system:
            messages.error(request, '系统级配置不能修改')
            return redirect('config_list')
        
        config.config_value = request.POST.get('config_value')
        config.save()
        messages.success(request, '配置更新成功')
        return redirect('config_list')
    
    return render(request, 'settings/config_form.html', {'config': config})


@login_required
def data_backup(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'backup':
            db_path = settings.DATABASES['default']['NAME']
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'cditams_backup_{timestamp}.sqlite3')
            
            shutil.copy2(db_path, backup_file)
            messages.success(request, f'数据备份成功: {backup_file}')
            
        elif action == 'restore':
            backup_file = request.POST.get('backup_file')
            if backup_file and os.path.exists(backup_file):
                db_path = settings.DATABASES['default']['NAME']
                shutil.copy2(backup_file, db_path)
                messages.success(request, '数据恢复成功，请重新启动系统')
            else:
                messages.error(request, '备份文件不存在')
        
        elif action == 'clean_logs':
            from apps.logs.models import SystemLog, SystemAssetLog
            from apps.accounts.models import LoginLog
            
            SystemLog.objects.all().delete()
            SystemAssetLog.objects.all().delete()
            LoginLog.objects.all().delete()
            messages.success(request, '日志数据已清理')
        
        elif action == 'clean_old_devices':
            from apps.assets.models import Device
            deleted = Device.objects.filter(status='scrapped').delete()[0]
            messages.success(request, f'已清理 {deleted} 条报废设备记录')
        
        return redirect('data_management')
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.sqlite3'):
                fpath = os.path.join(backup_dir, f)
                backups.append({'name': f, 'path': fpath, 'size': os.path.getsize(fpath), 'time': datetime.fromtimestamp(os.path.getmtime(fpath))})
    
    return render(request, 'settings/data_management.html', {'backups': backups})


@login_required
def data_management(request):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.sqlite3'):
                fpath = os.path.join(backup_dir, f)
                backups.append({'name': f, 'path': fpath, 'size': os.path.getsize(fpath), 'time': datetime.fromtimestamp(os.path.getmtime(fpath))})
    return render(request, 'settings/data_management.html', {'backups': backups})


@login_required
def download_backup(request):
    backup_file = request.GET.get('file')
    if backup_file and os.path.exists(backup_file):
        return FileResponse(open(backup_file, 'rb'), as_attachment=True)
    messages.error(request, '文件不存在')
    return redirect('data_management')


@login_required
def org_info(request):
    org = Organization.objects.first()
    
    if request.method == 'POST':
        if org:
            org.name = request.POST.get('name')
            org.short_name = request.POST.get('short_name')
            org.code = request.POST.get('code')
            org.contact_person = request.POST.get('contact_person')
            org.contact_phone = request.POST.get('contact_phone')
            org.contact_email = request.POST.get('contact_email')
            org.address = request.POST.get('address')
            org.website = request.POST.get('website')
            org.description = request.POST.get('description')
            if request.FILES.get('logo'):
                org.logo = request.FILES.get('logo')
            org.save()
        else:
            Organization.objects.create(
                name=request.POST.get('name'),
                short_name=request.POST.get('short_name'),
                code=request.POST.get('code'),
                contact_person=request.POST.get('contact_person'),
                contact_phone=request.POST.get('contact_phone'),
                contact_email=request.POST.get('contact_email'),
                address=request.POST.get('address'),
                website=request.POST.get('website'),
                description=request.POST.get('description'),
                logo=request.FILES.get('logo'),
            )
        messages.success(request, '企业信息更新成功')
        return redirect('org_info')
    
    return render(request, 'settings/org_form.html', {'org': org})


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        user.realname = request.POST.get('realname')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.gender = request.POST.get('gender')
        
        if request.FILES.get('avatar'):
            user.avatar = request.FILES.get('avatar')
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, '个人信息更新成功')
        return redirect('profile')
    
    return render(request, 'settings/profile.html', {'user': user})
