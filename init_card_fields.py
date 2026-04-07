import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.assets.models import DeviceField

# 设置默认卡片显示字段
card_fields = ['asset_no', 'device_no', 'name', 'model', 'secret_level', 
               'department', 'user', 'location', 'status']

print("开始设置默认卡片显示字段...")

for field_key in card_fields:
    try:
        field = DeviceField.objects.get(field_key=field_key)
        if not field.is_card_visible:
            field.is_card_visible = True
            field.save()
            print(f"已设置 {field.name}({field_key}) 为卡片显示")
        else:
            print(f"{field.name}({field_key}) 已经是卡片显示")
    except DeviceField.DoesNotExist:
        print(f"警告: 未找到字段 {field_key}")

print("默认卡片显示字段设置完成!")
