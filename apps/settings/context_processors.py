from apps.settings.models import SystemConfig


def system_config(request):
    """提供系统配置到模板上下文"""
    try:
        system_short_name = SystemConfig.objects.get(config_key='system_short_name').config_value
    except SystemConfig.DoesNotExist:
        system_short_name = 'CDITAMS'
    
    return {
        'system_short_name': system_short_name,
    }
