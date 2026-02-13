import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cditams.settings')
django.setup()

from apps.assets.models import AssetCategory

def init_categories():
    print("初始化资产分类...")
    
    AssetCategory.objects.all().delete()
    
    xcd = AssetCategory.objects.create(name='西安驰达', code='XACD', level=1, description='西安驰达飞机零部件制造股份有限公司')
    xys = AssetCategory.objects.create(name='西安优盛', code='XAYS', level=1, description='西安优盛航空科技有限公司')
    
    zcd_xcd = AssetCategory.objects.create(name='总经办', code='XACD-Z', level=2, parent=xcd)
    zcd_xys = AssetCategory.objects.create(name='总经办', code='XAYS-Z', level=2, parent=xys)
    
    jsj_xcd = AssetCategory.objects.create(name='计算机', code='XACD-Z-001', level=3, parent=zcd_xcd)
    jsj_xys = AssetCategory.objects.create(name='计算机', code='XAYS-Z-001', level=3, parent=zcd_xys)
    
    bg_xcd = AssetCategory.objects.create(name='办公设备', code='XACD-Z-002', level=3, parent=zcd_xcd)
    bg_xys = AssetCategory.objects.create(name='办公设备', code='XAYS-Z-002', level=3, parent=zcd_xys)
    
    xx_xcd = AssetCategory.objects.create(name='信息设备', code='XACD-Z-003', level=3, parent=zcd_xcd)
    xx_xys = AssetCategory.objects.create(name='信息设备', code='XAYS-Z-003', level=3, parent=zcd_xys)
    
    AssetCategory.objects.create(name='台式机', code='XACD-Z-001-001', level=4, parent=jsj_xcd)
    AssetCategory.objects.create(name='笔记本', code='XACD-Z-001-002', level=4, parent=jsj_xcd)
    AssetCategory.objects.create(name='显示器', code='XACD-Z-001-003', level=4, parent=jsj_xcd)
    AssetCategory.objects.create(name='其他', code='XACD-Z-001-004', level=4, parent=jsj_xcd)
    
    AssetCategory.objects.create(name='台式机', code='XAYS-Z-001-001', level=4, parent=jsj_xys)
    AssetCategory.objects.create(name='笔记本', code='XAYS-Z-001-002', level=4, parent=jsj_xys)
    AssetCategory.objects.create(name='显示器', code='XAYS-Z-001-003', level=4, parent=jsj_xys)
    AssetCategory.objects.create(name='其他', code='XAYS-Z-001-004', level=4, parent=jsj_xys)
    
    AssetCategory.objects.create(name='空调', code='XACD-Z-002-001', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='打印机', code='XACD-Z-002-002', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='扫描仪', code='XACD-Z-002-003', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='传真机', code='XACD-Z-002-004', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='投影仪', code='XACD-Z-002-005', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='交换机', code='XACD-Z-002-006', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='平板一体机', code='XACD-Z-002-007', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='照相机', code='XACD-Z-002-008', level=4, parent=bg_xcd)
    AssetCategory.objects.create(name='其他', code='XACD-Z-002-009', level=4, parent=bg_xcd)
    
    AssetCategory.objects.create(name='空调', code='XAYS-Z-002-001', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='打印机', code='XAYS-Z-002-002', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='扫描仪', code='XAYS-Z-002-003', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='传真机', code='XAYS-Z-002-004', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='投影仪', code='XAYS-Z-002-005', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='交换机', code='XAYS-Z-002-006', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='平板一体机', code='XAYS-Z-002-007', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='照相机', code='XAYS-Z-002-008', level=4, parent=bg_xys)
    AssetCategory.objects.create(name='其他', code='XAYS-Z-002-009', level=4, parent=bg_xys)
    
    AssetCategory.objects.create(name='服务器', code='XACD-Z-003-001', level=4, parent=xx_xcd)
    AssetCategory.objects.create(name='存储器', code='XACD-Z-003-002', level=4, parent=xx_xcd)
    AssetCategory.objects.create(name='监控设备', code='XACD-Z-003-003', level=4, parent=xx_xcd)
    AssetCategory.objects.create(name='监控系统', code='XACD-Z-003-004', level=4, parent=xx_xcd)
    AssetCategory.objects.create(name='其他', code='XACD-Z-003-005', level=4, parent=xx_xcd)
    
    AssetCategory.objects.create(name='服务器', code='XAYS-Z-003-001', level=4, parent=xx_xys)
    AssetCategory.objects.create(name='存储器', code='XAYS-Z-003-002', level=4, parent=xx_xys)
    AssetCategory.objects.create(name='监控设备', code='XAYS-Z-003-003', level=4, parent=xx_xys)
    AssetCategory.objects.create(name='监控系统', code='XAYS-Z-003-004', level=4, parent=xx_xys)
    AssetCategory.objects.create(name='其他', code='XAYS-Z-003-005', level=4, parent=xx_xys)
    
    count = AssetCategory.objects.count()
    print(f"已创建 {count} 条分类数据")
    
    print("\n分类结构验证:")
    for cat in AssetCategory.objects.filter(level=1):
        print(f"  {cat.name} ({cat.code})")
        for child in cat.children.all():
            print(f"    └─ {child.name} ({child.code})")
            for child2 in child.children.all():
                print(f"      └─ {child2.name} ({child2.code})")
                for child3 in child2.children.all():
                    print(f"        └─ {child3.name} ({child3.code})")

if __name__ == '__main__':
    init_categories()
