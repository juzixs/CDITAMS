"""
权限上下文处理器
将用户权限添加到所有模板上下文
"""


def user_permissions(request):
    """将用户权限添加到模板上下文"""
    if hasattr(request, 'user_permissions'):
        return {
            'user_permissions': request.user_permissions,
            'user_perm_set': set(request.user_permissions),
        }
    
    # 如果中间件没有处理，则在这里处理
    if hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
        perms = _get_user_permissions(user)
        return {
            'user_permissions': perms,
            'user_perm_set': set(perms),
        }
    
    return {
        'user_permissions': [],
        'user_perm_set': set(),
    }


def _get_user_permissions(user):
    """获取用户权限列表"""
    from apps.accounts.models import Permission
    
    # 超级管理员或拥有superuser/admin角色的用户拥有所有权限
    if user.is_superuser:
        return list(Permission.objects.values_list('code', flat=True))
    
    # 检查是否是超级管理员或管理员角色
    if user.role and user.role.code in ('superuser', 'admin'):
        return list(Permission.objects.values_list('code', flat=True))
    
    # 普通用户从角色获取权限
    if user.role:
        return list(user.role.permissions.values_list('code', flat=True))
    
    return []
