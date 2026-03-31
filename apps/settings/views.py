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


def get_config_value(key, default=None):
    """获取配置值，自动根据类型转换"""
    try:
        config = SystemConfig.objects.get(config_key=key)
        value = config.config_value
        if config.value_type == 'int':
            return int(value) if value else default
        elif config.value_type == 'boolean':
            return value.lower() in ('true', '1', 'yes')
        elif config.value_type == 'json':
            import json
            return json.loads(value) if value else default
        return value if value else default
    except (SystemConfig.DoesNotExist, ValueError):
        return default


@login_required
def config_list(request):
    group = request.GET.get('group', 'basic')
    groups = SystemConfig.GROUP_CHOICES
    configs = SystemConfig.objects.filter(config_group=group)
    return render(request, 'settings/config_list.html', {
        'configs': configs,
        'groups': groups,
        'current_group': group
    })


@login_required
def config_save(request):
    if request.method == 'POST':
        updated_count = 0
        for key, value in request.POST.items():
            if key.startswith('config_value_'):
                pk = key.replace('config_value_', '')
                try:
                    config = SystemConfig.objects.get(pk=pk, is_system=False)
                    if config.value_type == 'boolean':
                        # 处理布尔值（checkbox 提交时，如果未勾选则值为 'false'，勾选则有两个值）
                        checkbox_values = request.POST.getlist(key)
                        config.config_value = 'true' if 'true' in checkbox_values else 'false'
                    else:
                        config.config_value = value
                    config.save()
                    updated_count += 1
                except (SystemConfig.DoesNotExist, ValueError):
                    pass
        
        if updated_count > 0:
            messages.success(request, f'配置保存成功，已更新 {updated_count} 项配置')
        else:
            messages.info(request, '没有配置项被修改')
    
    # 获取当前分组并重定向
    referer = request.META.get('HTTP_REFERER', '')
    if 'group=' in referer:
        import re
        match = re.search(r'group=(\w+)', referer)
        if match:
            group = match.group(1)
            return redirect(f'/settings/configs/?group={group}')
    
    return redirect('config_list')


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
    from apps.accounts.models import Department
    
    user = request.user
    if request.method == 'POST':
        user.realname = request.POST.get('realname')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.gender = request.POST.get('gender')
        user.department_id = request.POST.get('department') or None
        
        if request.FILES.get('avatar'):
            user.avatar = request.FILES.get('avatar')
        
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password:
            if password != confirm_password:
                messages.error(request, '两次密码输入不一致')
                return redirect('profile')
            user.set_password(password)
        
        user.save()
        messages.success(request, '个人信息更新成功')
        return redirect('profile')
    
    departments = Department.objects.all()
    return render(request, 'settings/profile.html', {'user': user, 'departments': departments})
