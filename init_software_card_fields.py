import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.assets.models import SoftwareField

print("开始设置默认软件卡片显示字段...")

card_fields = ['name', 'asset_no', 'device_no', 'version', 'vendor', 
               'license_type', 'license_count', 'price', 'is_fixed', 'asset_card_no', 'description']

for field_key in card_fields:
    try:
        field = SoftwareField.objects.get(field_key=field_key)
        if not field.is_card_visible:
            field.is_card_visible = True
            field.save()
            print(f"已设置 {field.name}({field_key}) 为卡片显示")
        else:
            print(f"{field.name}({field_key}) 已经是卡片显示")
    except SoftwareField.DoesNotExist:
        print(f"警告: 未找到字段 {field_key}")

print("默认软件卡片显示字段设置完成!")