from django.db import migrations

def update_device_status(apps, schema_editor):
    """将维修中状态转换为故障状态"""
    Device = apps.get_model('assets', 'Device')
    # 将所有维修中的设备状态改为故障
    Device.objects.filter(status='repairing').update(status='fault')

def reverse_update_device_status(apps, schema_editor):
    """无法反向迁移，因为维修中状态已被移除"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0012_change_grid_default'),
    ]

    operations = [
        migrations.RunPython(update_device_status, reverse_update_device_status),
    ]
