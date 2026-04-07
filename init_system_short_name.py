import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.settings.models import SystemConfig

print("开始添加系统简称配置...")

# 检查是否已存在系统简称配置
if not SystemConfig.objects.filter(config_key='system_short_name').exists():
    SystemConfig.objects.create(
        config_key='system_short_name',
        config_value='CDITAMS',
        value_type='string',
        config_group='basic',
        description='系统简称',
        is_system=False
    )
    print("已添加系统简称配置")
else:
    print("系统简称配置已存在")

print("完成!")
